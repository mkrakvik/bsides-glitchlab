# What is Fault Injection?

Fault injection, also known as glitching, is a technique used to bypass security checks in micro controllers by intentionally pushing the micro controller beyond its normal operating conditions, causing it to behave unpredictably or skip critical instructions.

## What can happen when faults are injected?

1. **Instruction Skipping:** A well-timed voltage glitch or clock glitch can cause the micro controller to skip instructions. This can be exploited to bypass a security check or authentication step, allowing unauthorized access to protected functions.

2. **Changing Register Values:** Fault injection can modify values in CPU registers during execution. For instance, if a comparison operation is altered, it may change the outcome of a decision, such as bypassing a conditional branch or forcing a jump to malicious code.

3. **Bypassing Memory Protections:** Faults can be injected during memory operations to cause incorrect reads or writes. This might allow an attacker to overwrite key data, such as altering return addresses, leading to arbitrary code execution.

4. **Corrupting Program Counters:** By manipulating the program counter, an attacker can divert the execution flow to unintended code regions, such as areas that shouldn’t be reachable under normal conditions, potentially executing harmful or unintended operations.

## What kind of faults can be injected into a system?

1. **Voltage Fault Injection**: Briefly and precisely lowering or raising the voltage supplied to the micro controller to cause a fault in its operation. This could cause instruction skipping, bit flipping, memory corruption, or bypassing security checks.
2. **Clock Fault Injection**: Slow down, speed up or delay the micro controller's clock signal to disrupt the timing of operations.
3. **Electromagnetic Fault Injection (EMFI)**: Expose the micro controller to electromagnetic pulses. The induced energy can corrupt memory, data bus, or control logic of the micro controller.
4. **Laser Fault Injection**: A laser with a precisely controlled wavelength and power can be used to disrupt the semiconductor material of the micro controller at the transistor level. This can cause transient faults to memory cells or logic gates.

# Building a voltage glitching device

To perform a voltage glitching attack, we need to be able to "turn the power off" of the micro controller for some time, and then "turn it back on" again. The main challenge here is to figure out for how long we can leave the micro controller without power, such that it will keep running when we give it power again (as opposed to just blacking out, crashing or re-starting).

So, conceptually, what we will be building is a programmable on-off switch, that can toggle really fast.

![Switch and switch controller](https://s1.gifyu.com/images/SBFE9.gif)

For the on-off switch itself, we'll be using a MOSFET that reacts very quickly, and for the "switch operator" (which is responsible for flipping the on-off switch), we'll be using a micro controller.

There are products, like the ChipWhisperer range, that are designed for this task, but they can be expensive or challenging to acquire, so for our demo we are building a simple voltage glitching device using inexpensive (and accessible) parts.

For the on-off switch itself, we'll be using the ZXMN2F34FH N-channel MOSFET (others like the AO3400 can also be used). It is important that the MOSFET has a short turn on/off delay/rise/fall time.

![N-Channel MOSFET](https://s11.gifyu.com/images/SBUR5.jpg)

As the "switch operator", we'll be using an RP2040-Zero, which is based on the RP2040 micro controller.

![RP2040-Zero](https://s11.gifyu.com/images/SBURO.jpg)

The reason for using the RP2040 micro controller is because of it's Programmable IO (PIO) state machines. PIO allows for building a device that can toggle GPIO pins very fast (less than 10ns), compared to traditional micro controllers.

| Framework | Single toggle duration |
| -|-
| MicroPython | 15000 ns |
| Arduino | 500 ns |
| RP2040 PIO | 10 ns |
 
Test was performed on a RP2040-Zero board with default clock speed.

Adding some bells and whistles, such as a serial interface for monitoring our target, a reset pin so that we can programmatically reset the target and a few test points for hooking up our oscilloscope, we end up with a board like this:

![rp2040 glitcher](https://s1.gifyu.com/images/SBFl3.jpg)

# Our target device and firmware

## Target hardware

For our demo, we'll be targeting the STM32 micro controller (which is based on the Arm Cortex-M processor), on the "Blue Pill" development board.

![enter image description here](https://s1.gifyu.com/images/SBFcV.png)

## Target firmware

Our target firmware is specifically crafted for a fault injection attack that is not sensitive to the glitching offset, ie we can in practice introduce the fault at any time once it has booted. It's a simple loop that increments a counter, and if the counter value is unexpected, we break out of the loop (which in _theory_ should never happen).
```c
#include <Arduino.h>

void setup() {
  Serial.begin(9600);    // TX is on A2 pin for the Blue Pill board by default
  pinMode(PC13, OUTPUT); // this is the internal LED
}

void loop() {
  int loops = 0;
  int count = 0;
  int i = 0;
  int j = 0;

  digitalWrite(PC13, LOW);  // turn the LED on (active-low)

  while(true) {
    count = 0;
    i = 0;
    j = 0;
    for(i=0; i < 5000; i++) {
      for(j=0; j < 5000; j++) {
        count++;
      }
    }
    Serial.print(count);
    Serial.print(" ");
    Serial.print(i);
    Serial.print(" ");
    Serial.print(j);
    Serial.print(" ");
    Serial.println(loops++);

    if(count != 25000000)
      break;
  }

  // In theory, we should never get to this point
  Serial.println("#######");
  Serial.println("SUCCESSFUL GLITCH");
  Serial.println("#######");

  // blink the LED
  while(true) {
    digitalWrite(PC13, HIGH);
    delay(500);              
    digitalWrite(PC13, LOW);
    delay(500);
  }
}
```

## Where to glitch?

When trying to do a voltage glitching attack against a micro controller, it's most effective to target the power domains closest to the core, rather than the main power rail, as this offers more precise control over the critical operations we aim to disrupt.

It’s important to review the micro controller's datasheet to understand the various power domains and how they are intended to be implemented. When evaluating the target board, pay close attention to decoupling capacitors connected to these power domains, as they often provide convenient points for injecting glitches.

In the case of the STM32 Blue Pill board, most VDD inputs share the same power rail with multiple decoupling capacitors. This means we can experiment with injecting glitches at different points along the power rail to determine which location gives the best results. To get the best results, it's recommended to inject the glitch as physically close to the core as possible.

In my experience, injecting at the **C6** capacitor consistently produces positive results. This capacitor is relatively large, which makes it easier to attach a wire to it. Since we’re pulling the line to ground, make sure that the wire is connected to the positive side of the capacitor.

## Hooking it up

It is recommended to provide the target with a stable power supply, so we connect our lab PSU with 3.3V to the 3V3 power rail at the short end of the board.

We then connect the ground pins on our glitching device and the target device, the reset pins and the serial TX (A2 on the target board) to the glitcher's RX pin. And last but not least, we connect the wire on the C6 capacitor to the glitch pin on the glitching device.

| What   | Blue Pill | Glitcher
|--------|-----------|---------
| Serial | A2 | RX
| VDD    | C6 | Glitch Target
| Ground | GND | GND
| Reset  | R | RST

There are two test points on the glitcher board, "Glitch Enable" and "Glitch Target". We connect two oscilloscope probes to these points to monitor the glitches.

**Glitch Enable** monitors the output signal from the RP2040-Zero sent to the MOSFET, and serves as a nice trigger point for the scope. 

**Glitch Target** monitors the actual effect of the glitch (the line being pulled down to ground). Here you should see the voltage regulator and capacitors working to recover from the glitches.

## Using the glitcher

Once everything is hooked up, we connect the USB-C cable to the glitching device.

The glitching device runs MicroPython, which is a Python implementation that runs on the bare metal of the RP2040.

The `rp-glitcher/glitch.py` script can be loaded onto this and will expose a `Target`-object that allows you to interact with the STM32 target (inject glitches, reset the target board and read from serial).

```python

t.read()
t.reset()
t.glitch(20)
t.glitch_loop(5, 20)
```