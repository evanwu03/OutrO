

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