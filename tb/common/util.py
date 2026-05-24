



def get_packed_field(handle, start, stop=None):
    full_value = handle.value
    if stop is None:
        return full_value[start]
    else:
        return full_value[start:stop]


def pack_decoded(
    *,
    valid=0,
    cond=0,
    instr_class=0,
    rn=0,
    rm=0,
    rd=0,
    alu_opcode=0,
    set_cond=0,
    uses_imm=0,
    op2=0,
    offset=0,
    pre_index=0,
    offset_dir=0,
    is_byte=0,
    write_back=0,
    is_load=0,
    is_branch=0,
    is_link=0,
):
    fields = [
        (valid,       1),
        (cond,        4),
        (instr_class, 2),
        (rn,          4),
        (rm,          4),
        (rd,          4),
        (alu_opcode,  4),
        (set_cond,    1),
        (uses_imm,    1),
        (op2,         12),
        (offset,      32),
        (pre_index,   1),
        (offset_dir,  1),
        (is_byte,     1),
        (write_back,  1),
        (is_load,     1),
        (is_branch,   1),
        (is_link,     1),
    ]

    value = 0
    for field_value, width in fields:
        value = (value << width) | (int(field_value) & ((1 << width) - 1))

    return value

def set_decoded(dut, **kwargs):
    dut.i_decoded.value = pack_decoded(**kwargs)