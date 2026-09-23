# -*- coding: utf-8 -*-
"""
一键灌入 12 条模拟测试工单。
覆盖：正常故障 / 紧急故障 / 描述模糊口语化 / 描述极短 /
      知识库外故障 / 同义不同表达 / 空描述与超长输入异常。

运行：
    python test_cases/seed_test_data.py
重复运行会先清空旧工单再灌入，保证可重复。
"""
import os
import sys

# 把项目根目录加入 import 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db
import ai_engine

# 12 条测试工单：(报修人, 设备, 位置, 描述, 联系方式, 分类说明)
CASES = [
    ("张三", "STM32开发板", "实验室302",
     "今天实验课要用，板子下载不进去程序，串口也没反应，急！",
     "13800000001", "正常-紧急"),
    ("李四", "显示器", "实验室301",
     "开机后屏幕不亮，提示无信号，主机风扇在转",
     "13800000002", "正常"),
    ("王五", "台式机", "实验室305",
     "电脑经常蓝屏自动重启，蓝屏代码是 0x0000007B",
     "13800000003", "正常"),
    ("赵六", "笔记本", "实验室303",
     "WiFi 连不上，频繁掉线，手机连同一个路由器正常",
     "13800000004", "正常"),
    ("钱七", "键盘", "实验室304",
     "USB 键盘插上去没反应，打不了字",
     "13800000005", "正常"),
    ("孙八", "投影仪", "会议室",
     "HDMI 接了但投影显示无信号，按遥控器也切不动",
     "13800000006", "正常"),
    ("周九", "打印机", "实验室前台",
     "打印机卡纸了，而且显示脱机，任务队列里堆了好多任务",
     "13800000007", "正常"),
    ("吴十", "音箱", "实验室302",
     "电脑播放视频没有声音，音量已经拉满了",
     "13800000008", "正常"),
    ("郑十一", "台式机", "实验室306",
     "这台电脑卡得要死，点个半天才反应，风扇还呼呼响",
     "13800000009", "模糊/口语化"),
    ("王十二", "显示器", "实验室307",
     "老样子",
     "13800000010", "描述极短/信息缺失"),
    ("冯十三", "示波器", "硬件调试间",
     "示波器波形显示一直抖动，校准不准，测出来的值飘",
     "13800000011", "知识库外"),
    ("褚十四", "台式机", "实验室308",
     "开机用一会就蓝屏了，烦死了",
     "13800000012", "同义不同表达（与T03同故障）"),
]


def seed(clean=True):
    db.init_db()
    if clean:
        conn = db.get_conn()
        conn.execute("DELETE FROM workorders")
        conn.commit()
        conn.close()

    created = []
    for reporter, device, location, desc, contact, tag in CASES:
        ai = ai_engine.analyze(reporter, device, location, desc, contact)
        new_id, ticket_no = db.create_workorder(
            reporter=reporter,
            device_name=device,
            location=location,
            description=desc,
            contact=contact,
            category=ai["category"],
            urgency=ai["urgency"],
            summary=ai["summary"],
            suggestion=ai["suggestion"],
            matched_kb=ai["matched_kb"],
            need_manual=ai["need_manual"],
        )
        created.append((ticket_no, tag, ai["category"], ai["urgency"], bool(ai["need_manual"])))
    return created


if __name__ == "__main__":
    rows = seed(clean=True)
    print(f"已灌入 {len(rows)} 条测试工单：")
    print(f"{'工单号':<18}{'分类':<16}{'类别':<14}{'紧急':<6}{'需人工'}")
    for r in rows:
        print(f"{r[0]:<18}{r[1]:<16}{r[2]:<14}{r[3]:<6}{r[4]}")
    print("\n当前数据库统计：", db.stats())
