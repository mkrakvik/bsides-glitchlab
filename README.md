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
