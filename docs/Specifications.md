

# Features 
- Harvard Architecture (separate data and instruction memory)
- Single issue frontend based on Tomasulo's Algorithm
- Reservation stations for integer operations
- 1 Instruction Queue
- 1 Common Data Bus (CDB): At most one result may be broadcast per cycle, so simultaneous FU completions require CDB arbitration
- Forwarding for RAW hazard resolution via CDB broadcasts
- 2 Functional Units (integer ALUs) 
- 1 Reorder Buffer (ROB) with in-order commit
- 1 Register Alias Table (RAT) with tag based register renaming
- 1 Load Buffer and basic store handling through the ROB
- 1 Register file
- 1 Instruction Decoder
- Static branch prediction with flush-based recovery on mispredict
- Simple memory unit for data


# Nice to have
- I/D Cache 
- Translation Lookaside buffer (TLB)
- Floating point unit (FPU) to execute IEEE754 arithmetic
- 2 CDB in the future
- Advanced branch prediction (needs research)


# Timeline
1. fetch / decode / rename
2. RS + RAT + ROB interaction
3. ALU execution + CDB forwarding
4. in-order commit
5. loads
6. branch recovery


# TBD
- ROB Depth
- Number of RS entires
- Load Buffer depth
- Register count
- Instruction format (ISA)
- ROB + RAT + RS Field format
- I/D Cache Depth (After essentials are completed)