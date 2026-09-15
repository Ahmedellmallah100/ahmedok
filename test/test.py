why 1 hour for test ???
Pasted text(20260915-211509).txt
Document

آه، راجعت الـtest نفسه، والسبب واضح جدًا: أنت عامل SLOW_CLOCK_CYCLES = 500000، وده بيخلي الـtest يستنى 500 ألف clock cycle في كل خطوة تقريبًا.

والـclock عندك:

Clock(dut.clk, 10, unit="us")

يعني كل cycle = 10 µs.

الحساب

500,000 cycles × 10 µs = 5 seconds

وفي كل press_button() أنت بتعمل:

5 ثواني للـdebounce
5 ثواني بعد release

يعني 10 ثواني لكل button press.

وكل operation عندك تعمل:

Set A → 10 sec
Set B → 10 sec
Execute → 10 sec
Check display → حوالي 40 sec

= حوالي 70 ثانية لكل operation.

وأنت عندك 13 operation تقريبًا، بالإضافة لاختبارات الـdisplay والـanode.

إجمالي simulation time النظري ≈ 16 دقيقة حتى على RTL simulation.

طيب ليه عندك ظاهر 1h 28s؟

لو ده وقت الـwall-clock الحقيقي اللي استغرقه الـgate-level test، فالموضوع أسوأ لأن gate-level simulation أبطأ جدًا من RTL.

خصوصًا إنك تعمل عدد ضخم جدًا من clock events:

500,000 cycles × مرات كثيرة جدًا

فالـtest مش فيه loop لا نهائي؛ المشكلة الأساسية هي إنك عامل debounce delay ضخم جدًا.

الحل

لو هدفك مجرد اختبار الـdesign، جرّب مثلًا:

SLOW_CLOCK_CYCLES = 5000

بدل:

SLOW_CLOCK_CYCLES = 500000

ساعتها كل wait:

5000 × 10 µs = 50 ms

بدل 5 seconds.

وده هيخلي الاختبار أسرع بحوالي:

100×

لكن مهم: لو 500000 هو فعلًا divider المطلوب في الـRTL، فالأفضل نعمل test-specific override للـsimulation بدل ما نغير الـdesign نفسه.

لو ده TinyTapeout gate-level test تحديدًا، أقدر أظبط لك الملف بحيث يحتفظ بالـ500,000 في الـdesign لكن الـgl_test يخلص في دقائق بدل الساعة+.

edit it

Done. I changed:

SLOW_CLOCK_CYCLES = 500000

to:

SLOW_CLOCK_CYCLES = 5000

This should make the test ~100× faster while keeping the same test structure.

Download the edited gl_test_fast.py 

gl_test_fast.py
Code
Pasted text(20260915-213135).txt
Document
fix it and why there are test fo letters and led and i remoove them

Yes — you're right. If you removed the LED and letters from your design, the test should not check internal signals like:

dut.core.led
dut.core.A1.letters

Those checks were still present in the previous test file.

I fixed it:

✅ SLOW_CLOCK_CYCLES = 5000
❌ Removed LED tests
❌ Removed letters tests
❌ Removed expected_letter from test_operation()
❌ Removed all check_internal_outputs() calls
✅ Kept ALU operation tests
✅ Kept 7-segment display tests
✅ Kept anode/multiplexing test

The display/anode checks are still relevant because your test explicitly tests the 7-segment output and four anodes.

Download the fixed gl_test_fixed.py 

gl_test_fixed.py
Code

Library
/
gl_test_fixed.py
999
152
153
154
155
156
157
158
159
160
161
162
163
164
165
166
167
168
169
170
171
172
173
174
175
176
177
178
179
180
181
182
183
184
185
186
187
188
189
190
191
192
193
194
195
196
197
198
199
200
201
202
203
204
205
206
207
208
209
210
211
212
213
214
215
216
217
218
219
220
221
222
223
224
225
226
227
228
229
230
231
232
233
234
235
236
237
238
239
240
241
242
243
244
# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
                digits[0] = digit


            elif an == 0b1101:
                digits[1] = digit


            elif an == 0b1011:
                digits[2] = digit


            elif an == 0b0111:
                digits[3] = digit


    return digits




# ============================================================
# Convert Display Digits to Integer
# ============================================================


def digits_to_number(digits):


    assert 0 in digits, "AN0 was not detected"
    assert 1 in digits, "AN1 was not detected"
    assert 2 in digits, "AN2 was not detected"


    ones = digits[0]
    tens = digits[1]
    hundreds = digits[2]


    return hundreds * 100 + tens * 10 + ones




# ============================================================
# Check Display Result
# ============================================================


async def check_display(dut, expected):


    digits = await read_display(dut)


    actual = digits_to_number(digits)


    assert actual == expected, (
        f"\nDISPLAY ERROR\n"
        f"Expected : {expected}\n"
        f"Actual   : {actual}\n"
        f"Digits   : {digits}"
    )


    dut._log.info(
        f"DISPLAY PASSED -> {actual}"
    )




# ============================================================
# Check All Anodes
# ============================================================


async def check_all_anodes(dut):


    seen = set()


    # Give the multiplexer enough time to visit
    # all four digits.
    for _ in range(4):


        await ClockCycles(
            dut.clk,
            SLOW_CLOCK_CYCLES
        )


        an = get_current_anode(dut)


        seen.add(an)


    expected = {
        0b1110,
        0b1101,
        0b1011,
        0b0111
    }


    assert expected.issubset(seen), (
        f"\nANODE ERROR\n"
        f"Expected: {expected}\n"
        f"Detected: {seen}"
    )


    dut._log.info(
        f"ALL 4 ANODES PASSED -> {seen}"
    )




# ============================================================
