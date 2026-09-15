import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_gate_level(dut):

    # Start clock
    cocotb.start_soon(
        Clock(dut.clk, 10, unit="us").start()
    )

    # Enable design
    dut.ena.value = 1

    # Initial inputs
    dut.ui_in.value = 0x00
    dut.uio_in.value = 0x00

    # Active-low reset
    dut.rst_n.value = 0

    # Let reset propagate
    await ClockCycles(dut.clk, 20)

    # Check fixed wrapper outputs
    oe = int(dut.uio_oe.value)

    assert oe == 0x78, (
        f"Wrong uio_oe after reset: "
        f"expected 0x78, got 0x{oe:02X}"
    )

    # Release reset
    dut.rst_n.value = 1

    await ClockCycles(dut.clk, 20)

    # Read outputs
    uio_out = int(dut.uio_out.value)
    uio_oe  = int(dut.uio_oe.value)

    # uio_oe[6:3] must always be outputs
    assert uio_oe == 0x78, (
        f"uio_oe wrong: expected 0x78, got 0x{uio_oe:02X}"
    )

    # uio_out[7] and uio_out[2:0] are hard-wired to zero
    assert (uio_out & 0x87) == 0, (
        f"Invalid fixed uio_out bits: 0x{uio_out:02X}"
    )

    # Change inputs just to make sure the top-level is alive
    for value in [0x00, 0x01, 0x55, 0xAA, 0xFF]:

        dut.ui_in.value = value
        await ClockCycles(dut.clk, 5)

    # Toggle push-button inputs
    dut.uio_in.value = 0x07
    await ClockCycles(dut.clk, 5)

    dut.uio_in.value = 0x00
    await ClockCycles(dut.clk, 5)

    cocotb.log.info("GATE-LEVEL TEST PASSED")