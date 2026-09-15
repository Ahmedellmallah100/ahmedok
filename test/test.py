import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles


# ============================================================
# Configuration
# ============================================================

# RTL:
# clk_divider toggles slow_clk every 250001 clk cycles.
SLOW_DIVIDER = 250002


# ============================================================
# 7 Segment Decoder
# ============================================================

SEGMENTS = {
    0x3F: 0,
    0x06: 1,
    0x5B: 2,
    0x4F: 3,
    0x66: 4,
    0x6D: 5,
    0x7D: 6,
    0x07: 7,
    0x7F: 8,
    0x6F: 9,
}


def decode_7seg(value):
    value = value & 0x7F
    return SEGMENTS.get(value)


# ============================================================
# Reset
# ============================================================

async def reset_dut(dut):

    dut.rst_n.value = 0
    dut.ena.value = 1

    dut.ui_in.value = 0
    dut.uio_in.value = 0

    await ClockCycles(dut.clk, 20)

    dut.rst_n.value = 1

    await ClockCycles(dut.clk, 20)

    cocotb.log.info("RESET PASSED")


# ============================================================
# Button
# ============================================================

async def press_button(dut, button):

    if button == 1:
        value = 0b00000001

    elif button == 2:
        value = 0b00000010

    elif button == 3:
        value = 0b00000100

    else:
        raise ValueError("Invalid button")

    # Press
    dut.uio_in.value = value

    # Hold long enough for slow_clk
    await ClockCycles(dut.clk, SLOW_DIVIDER)

    # Release
    dut.uio_in.value = 0

    # Allow debounce/state logic to update
    await ClockCycles(dut.clk, SLOW_DIVIDER)


# ============================================================
# Set A
# ============================================================

async def set_a(dut, value):

    cocotb.log.info(f"Setting A = {value}")

    dut.ui_in.value = value

    await press_button(dut, 1)


# ============================================================
# Set B
# ============================================================

async def set_b(dut, value):

    cocotb.log.info(f"Setting B = {value}")

    dut.ui_in.value = value

    await press_button(dut, 2)


# ============================================================
# Execute
# ============================================================

async def execute(dut):

    cocotb.log.info("Executing operation")

    # ADD = 001
    dut.ui_in.value = 1

    await press_button(dut, 3)


# ============================================================
# Read Anode
# ============================================================

def get_anode(dut):

    # IMPORTANT:
    #
    # wrapper:
    #
    # uio_out[3] = an[0]
    # uio_out[4] = an[1]
    # uio_out[5] = an[2]
    # uio_out[6] = an[3]
    #
    # Therefore an = uio_out[6:3]

    value = int(dut.uio_out.value)

    return (value >> 3) & 0xF


# ============================================================
# Read Segment
# ============================================================

def get_segment(dut):

    value = int(dut.uo_out.value)

    return value & 0x7F


# ============================================================
# Wait For Specific Digit
# ============================================================

async def wait_for_anode(dut, expected_anode, timeout_cycles):

    for _ in range(timeout_cycles):

        an = get_anode(dut)

        if an == expected_anode:
            return True

        await RisingEdge(dut.clk)

    return False


# ============================================================
# Read Ones Digit
# ============================================================

async def read_ones_digit(dut):

    # AN0 = 1110
    #
    # We only need the ones digit.
    #
    # This avoids waiting for all four display digits.

    cocotb.log.info("Waiting for ONES digit...")

    found = await wait_for_anode(
        dut,
        0b1110,
        SLOW_DIVIDER + 1000
    )

    assert found, (
        "AN0 (1110) was not detected"
    )

    seg = get_segment(dut)

    digit = decode_7seg(seg)

    cocotb.log.info(
        f"AN0 detected: SEG={seg:07b}, DIGIT={digit}"
    )

    assert digit is not None, (
        f"Unknown 7-segment pattern: {seg:07b}"
    )

    return digit


# ============================================================
# Main Gate-Level Test
# ============================================================

@cocotb.test()
async def test_alu(dut):

    cocotb.log.info("")
    cocotb.log.info("======================================")
    cocotb.log.info("   ALU GATE LEVEL TEST")
    cocotb.log.info("======================================")

    # Start clock
    cocotb.start_soon(
        Clock(
            dut.clk,
            10,
            unit="us"
        ).start()
    )

    # Reset
    await reset_dut(dut)

    # --------------------------------------------------------
    # A = 20
    # --------------------------------------------------------

    await set_a(dut, 20)

    # --------------------------------------------------------
    # B = 10
    # --------------------------------------------------------

    await set_b(dut, 10)

    # --------------------------------------------------------
    # ADD
    # --------------------------------------------------------

    await execute(dut)

    # --------------------------------------------------------
    # Read result
    # --------------------------------------------------------

    ones = await read_ones_digit(dut)

    cocotb.log.info(
        f"RESULT ONES DIGIT = {ones}"
    )

    # 20 + 10 = 30
    # Therefore ones digit must be 0.
    assert ones == 0, (
        f"ADD failed: expected ones digit 0, got {ones}"
    )

    cocotb.log.info("")
    cocotb.log.info("======================================")
    cocotb.log.info("       ALU TEST PASSED")
    cocotb.log.info("       20 + 10 = 30")
    cocotb.log.info("======================================")