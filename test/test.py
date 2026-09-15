import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


# ============================================================
# 7-Segment decoder
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
    value &= 0x7F
    return SEGMENTS.get(value, None)


# ============================================================
# Read display
# ============================================================

async def observe_display(dut, cycles=1100000):

    detected = {}

    for _ in range(cycles):

        an = int(dut.an.value) & 0xF
        seg = int(dut.out_seg.value) & 0x7F

        digit = decode_7seg(seg)

        if an == 0b1110:
            detected[0] = digit

        elif an == 0b1101:
            detected[1] = digit

        elif an == 0b1011:
            detected[2] = digit

        elif an == 0b0111:
            detected[3] = digit

        if set(detected.keys()) == {0, 1, 2, 3}:
            break

        await ClockCycles(dut.clk, 1)

    dut._log.info(f"ANODES/DIGITS DETECTED: {detected}")

    assert set(detected.keys()) == {0, 1, 2, 3}, (
        f"Not all 4 anodes detected. Detected: {detected}"
    )

    return detected


# ============================================================
# Button press
# ============================================================

async def press_button(dut, button):

    dut.uio_in.value = button

    # Debounce + enough time for the button to be processed
    await ClockCycles(dut.clk, 300000)

    dut.uio_in.value = 0

    await ClockCycles(dut.clk, 300000)


# ============================================================
# Set A
# ============================================================

async def set_a(dut, value):

    dut.sw.value = value

    # PB1
    await press_button(dut, 0b001)


# ============================================================
# Set B
# ============================================================

async def set_b(dut, value):

    dut.sw.value = value

    # PB2
    await press_button(dut, 0b010)


# ============================================================
# Execute operation
# ============================================================

async def execute_operation(dut, opcode):

    dut.sw.value = opcode

    # PB3
    await press_button(dut, 0b100)


# ============================================================
# Reset
# ============================================================

async def reset_dut(dut):

    dut.rst.value = 0
    dut.sw.value = 0
    dut.uio_in.value = 0

    await ClockCycles(dut.clk, 20)

    dut.rst.value = 1

    await ClockCycles(dut.clk, 20)


# ============================================================
# Test one operation
# ============================================================

async def test_operation(dut, a, b, opcode, name, expected):

    dut._log.info(
        f"TEST: {name} | A={a} B={b} OPCODE={opcode:03b}"
    )

    await set_a(dut, a)
    await set_b(dut, b)
    await execute_operation(dut, opcode)

    detected = await observe_display(dut)

    # Display is:
    # AN0 = ones
    # AN1 = tens
    # AN2 = hundreds
    #
    # AN3 is currently checked only as a multiplexing digit.

    ones = detected[0]
    tens = detected[1]
    hundreds = detected[2]

    displayed_value = (
        hundreds * 100 +
        tens * 10 +
        ones
    )

    dut._log.info(
        f"DISPLAY = {displayed_value}, EXPECTED = {expected}"
    )

    assert displayed_value == expected, (
        f"{name} failed: "
        f"displayed={displayed_value}, expected={expected}"
    )

    dut._log.info(f"PASS: {name}")


# ============================================================
# Main test
# ============================================================

@cocotb.test()
async def test_project(dut):

    dut._log.info("=== START ALU GATE-LEVEL TEST ===")

    # 100 kHz clock
    cocotb.start_soon(
        Clock(dut.clk, 10, unit="us").start()
    )

    # TinyTapeout enable
    dut.ena.value = 1

    # Reset
    await reset_dut(dut)

    dut._log.info("RESET PASS")

    # --------------------------------------------------------
    # ADD
    # --------------------------------------------------------

    await test_operation(
        dut,
        20,
        10,
        0b001,
        "ADD",
        30
    )

    # --------------------------------------------------------
    # SUB
    # --------------------------------------------------------

    await test_operation(
        dut,
        20,
        10,
        0b010,
        "SUB",
        10
    )

    # --------------------------------------------------------
    # ZERO
    # --------------------------------------------------------

    await test_operation(
        dut,
        0,
        0,
        0b001,
        "ZERO ADD",
        0
    )

    # --------------------------------------------------------
    # 8-bit overflow
    # 200 + 100 = 300
    # 300 mod 256 = 44
    # --------------------------------------------------------

    await test_operation(
        dut,
        200,
        100,
        0b001,
        "ADD OVERFLOW",
        44
    )

    dut._log.info("================================")
    dut._log.info("=== ALL TESTS PASSED ===")
    dut._log.info("================================")