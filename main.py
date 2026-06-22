# -*- coding: utf-8 -*-
"""
TODO-List 桌面应用启动入口。

直接运行 ``python main.py`` 即可启动应用。
"""

import sys

from src.gui import run_app


def main():
    """
    启动应用的主入口函数。

    Returns
    -------
    int
        应用程序退出状态码，0 代表正常退出。
    """
    return run_app()


if __name__ == "__main__":
    sys.exit(main())
