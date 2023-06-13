# stupid_bot

## HalfTrede MT5 (python)

open forex order by halftrend signal

## disclaimer (ข้อจำกัดความรับผิดชอบ)
- ผู้พัฒนาไม่สามารถรับผิดชอบ ความเสียหายที่เกิดจาก การใช้งาน บัค error หรือ อื่นๆ ได้ ผู้ใช้โปรแกรมต้องยอมรับความเสี่ยงที่เกิดขึ้นเอง โดย ทดลอง ทดสอบ ให้มั่นใจก่อนนำไปใช้ในการลงทุน
- ผู้พัฒนาไม่อนุญาติให้นำโปรแกรมไปแสวงหาผลประโยชน์จากบุคคลอื่น หากทราบ จะหยุดการพัฒนาและเผยแพร่โปรแกรมโดยทันที

## V1.0.4
- แก้บัค ><

## V1.0.3
- กำหนดค่า tp,sl เป็นค่า bib หรือเป็นเปอร์เซ็นโดยระบุ % ต่อท้าย เช่น sl = 10%
- check สัญญาณ macd ก่อนเปิด order
- เพิ่มการเปิด order ด้วยสัญญาน macd cross (MACD ตัด MACDs)

## V1.0.1
- กำหนด tp sl อัตโนมัติ ด้วย fibo (ค่า min max ของแท่งเทียนย้อนหลัง 100 แท่ง)
- trailing stop - ปรับ sl ตามราคาที่เปลี่ยนแปลง โดยรักษาระยะห่างระหว่าง sl กับ high ให้เท่ากับราคาตอนเปิด position
- martingale - กำหนดให้เบิ้ล lot ได้ 
    - martingale_factor = 1.0 จะเป็นการ คูณ lot ด้วยจำนวน loss สะสม
    - martingale_factor > 1.0 จะเป็นการ คูณ lot ด้วยจำนวน loss สะสม แบบ exponencial เช่น martingale_factor = 2 คือ 2 ยกกำลัง จำนวน loss สะสม

## config.ini (rename จาก config_sample.ini)

    [mt5]
    login = 
    password = 
    server = 

    [line]
    notify_token = 

    [app_config]
    ;# สามารถข้ามส่วนนี้ไปได้ โดยใช้ค่าที่กำหนดให้ได้เลย
    ;TIME_SHIFT = 5
    ;# level การบันทึก log file ทั่วไปให้ใช้แบบ INFO
    ;# CRITICAL 50, ERROR 40, WARNING 30, INFO 20, DEBUG 10, NOTSET 0
    ;LOG_LEVEL = 10
    ;# กำหนดรอบเวลาในแสดง update balancec และ trailing stop
    ;# 0=timeframe, 1=10, 2=15, 3=20, 4=30, 5=60, 6=timeframe/2 
    ;UB_TIMER_MODE = 1

    [setting]
    ;# 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d
    timeframe = 5m
    signal_index = -2
    magic_number = 999111

    symbols = XAUUSD, AUDUSD, GBPUSD, USDJPY, EURJPY, GBPAUD, AUDCAD, CADJPY, CADCHF, NZDJPY
    lot = 0.02
    deviation = 20

    atrlen = 100
    amplitude = 3
    channel_deviation = 2

    ;check สัญญาณ macd ก่อนเปิด order default = on
    ; confirm_macd = off

    ;เพิ่มการเปิด order ด้วยสัญญาน macd cross (MACD ตัด MACDs) default = off
    ; macd_cross = on

    martingale_mode = on
    martingale_factor = 1.0
    martingale_max = 16
    ;ถ้า martingale_factor > 1.0 จะเป็นการเพิ่ม lot ตามเทคนิค martingale (ทวีคูณ)
    ;martingale_factor = 2.0
    ;martingale_max = 8

    auto_tpsl = on
    sl = 150
    tp = 300
    ;สามารถกำหนดค่าเป็นเปอร์เซ็นต์ได้
    ;sl = 0.7%
    ;tp = 1.2%

    trailing_stop = on