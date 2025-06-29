#!/usr/bin/env python3
"""
サブプロセスで関数を実行するシンプルなサンプル
"""

import multiprocessing
import time
import os


def simple_worker():
    """
    シンプルなワーカー関数：3秒スリープするだけ
    """
    pid = os.getpid()
    print(f"サブプロセス開始 (PID: {pid})")
    time.sleep(3)
    print(f"サブプロセス完了 (PID: {pid})")


def main():
    """
    メイン関数：サブプロセスを実行
    """
    print("サブプロセス実行サンプル")
    print("=" * 30)
    
    print(f"メインプロセス PID: {os.getpid()}")
    
    # サブプロセスを作成して実行
    process = multiprocessing.Process(target=simple_worker)
    
    print("サブプロセスを開始します...")
    process.start()
    
    print("サブプロセスの完了を待機中...")
    process.join()
    
    print("サブプロセスが完了しました")


if __name__ == "__main__":
    main()