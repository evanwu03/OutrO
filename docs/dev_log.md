

# Week 1

## 4/24/2026
- Plan to implement the ALU, instruction decoder, and instruction queue first before adding out of order features
- Focus on the instruction execution path first
- The CPU shall execute two instructions per cycle therefore it follow a multi-issue instruction system.

## 5/6/2026
- I learned how to writer Cocotb pytest runners for testing because it is difficult to pass parameters using makefile.
- Implemented the following and tested with Cocotb: 
  - Register file
  - Instruction memory
  - Data memory
  

- Currently designing the instruction fetch unit. The IF unit will need to be 2-wide and will need support a multi-port instruction FIFO.
- I should use an interface for the Common Data Bus

### TBD
- After IF unit need to work on the:
  - Instruction decoder 
  - Execution unit: 
    - Reorder buffer
    - Reservation stations & Register Alias Table
    - Common databus

Decoder → RAT/ROB allocation → RS insert → ALU execute → CDB broadcast → ROB commit


## 5/9/2026

According to Chapter 3.8 of Computer Architecture, Sixth Edition, A Quantitive approach, Multi-issue scalar processors can be approached in the following methods:

1. VLIW (Very long instruciton words)
2. Static scheduling in-order
3. Dynamic scheduling (out-of order with or with speculation)

For this project, option 3 seems to be the most applicable. 
On pg. 222, they note some approaches and limitations:

```
Two different approaches have been used to issue multiple instructions per clock in a dynamically scheduled processor, and both rely on the observation that the key is assigning a reservation station and updating the pipeline control tables. One approach is to run this step in half a clock cycle so that two instructions can be processed in one clock cycle; this approach cannot be easily extended to handle four instructions per clock, unfortunately. 
``` 

Alternatively you must develop logic to handle 2 or more instructions at once and handle dependencies between those instructions. 


### Instruction Fetch Unit updates
- After some weird glitches with the reset() function throwing off the instruction fetch logic by one cycle during testing, 
I am much more confident it fetches as intended. Learned a good deal about creating a multi-port FIFO. Suprisingly not too different than a single-port FIFO, just need extra logic to ensure you never write to a full FIFO or read from an empty FIFO.

### Decoder
- Now is about time that I define the decode stage of the processor. Compared to my first CPU where
I primarily relied on long list of outputs for every single action that should be taken based on the instruction type, I am using a packet struct to simplify the ports significantly. 

### Understanding the pipeline 
- Somtimes I feel like I have some trouble wrapping my head, not really just about what each block does but about how what happens on the data boundary, so I asked Chatgpt to help summarize each stage in the pipeline.
  
Instruction fetch:
  cares about PC, instruction bits, valid, FIFO ordering

Decode:
  cares about interpreting raw bits

Rename/dispatch:
  cares about architectural registers, RAT, ROB tags, dependencies

Reservation station:
  cares about operand readiness, operand values, tags, operation type

ROB:
  cares about program order, destination register, result readiness, commit

CDB:
  cares about broadcasting completed tag + value


## 5/20/2026
Up to this point I've completed the following: 
- Instruction fetch unit
- Instruction decoder
- Register Alias Table (RAT)
- Dispatch unit
- Reservation stations

Today I will focus on writing tests for the reservation station 
and refactoring existing tests, so they are easier to modify 
and share standard helper functions.

## 5/24/2026
- Significant progress made on refactoring cocotb tests
- Plan to study formal verification

### To-do:
- ~~Implement Address unit~~
- Implement Load buffer

- need to implement the address field as they are required for stores when ROB commits to memory
