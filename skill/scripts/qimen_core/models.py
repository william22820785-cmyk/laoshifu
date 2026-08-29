"""
数据模型 — 奇门遁甲排盘结果

按架构文档 §4 定义的 PanResult / Sizhu / Jushu / Xunshou / ZhifuZhishi / GongData
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Sizhu:
    """四柱"""
    year_gan: str       # 年干
    year_zhi: str       # 年支
    month_gan: str
    month_zhi: str
    day_gan: str
    day_zhi: str
    hour_gan: str
    hour_zhi: str

    @property
    def year(self) -> str:
        return self.year_gan + self.year_zhi

    @property
    def month(self) -> str:
        return self.month_gan + self.month_zhi

    @property
    def day(self) -> str:
        return self.day_gan + self.day_zhi

    @property
    def hour(self) -> str:
        return self.hour_gan + self.hour_zhi

    def to_dict(self) -> dict:
        return {
            "年柱": self.year,
            "月柱": self.month,
            "日柱": self.day,
            "时柱": self.hour,
        }


@dataclass
class Jushu:
    """局数信息"""
    ju_num: int
    yin_yang: str                  # "阳遁" / "阴遁"
    jieqi: str                     # 节气名
    method: str = "拆补"           # "拆补" / "置闰"
    yuan: str = "上元"             # "上元" / "中元" / "下元"

    def to_dict(self) -> dict:
        return {
            "局数": self.ju_num,
            "阴阳遁": self.yin_yang,
            "节气": self.jieqi,
            "计算方法": self.method,
            "元": self.yuan,
        }


@dataclass
class Xunshou:
    """旬首信息"""
    xunshou: str             # 甲子/甲戌/...
    yinyi: str               # 隐仪天干
    kong_zhi: list[str]      # 空亡地支
    kong_gong: list[int]     # 空亡宫位
    masa: str = ""           # 马星地支

    def to_dict(self) -> dict:
        return {
            "旬首": self.xunshou,
            "隐仪": self.yinyi,
            "空亡地支": self.kong_zhi,
            "空亡宫位": self.kong_gong,
            "马星": self.masa,
        }


@dataclass
class ZhifuZhishi:
    """值符值使"""
    zhifu_xing: str          # 值符星名
    zhifu_xing_gong: int     # 值符星原始宫位
    zhifu_luo_gong: int      # 值符落宫
    zhishi_men: str          # 值使门名
    zhishi_men_gong: int     # 值使门原始宫位
    zhishi_luo_gong: int     # 值使落宫

    def to_dict(self) -> dict:
        return {
            "值符星": self.zhifu_xing,
            "值符星原始宫": self.zhifu_xing_gong,
            "值符落宫": self.zhifu_luo_gong,
            "值使门": self.zhishi_men,
            "值使门原始宫": self.zhishi_men_gong,
            "值使落宫": self.zhishi_luo_gong,
        }


@dataclass
class GongData:
    """单个九宫格数据"""
    gong_num: int
    gong_name: str
    fangwei: str
    wuxing: str
    dipan_gan: str
    tianpan_gan: str
    jiuxing: str
    bamen: str
    bashen: str
    is_kong: bool = False
    men_po: bool = False
    fan_yin: bool = False
    fu_yin: bool = False
    geju: list[str] = field(default_factory=list)  # 格局列表
    beizhu: str = ""                                 # 备注

    def to_dict(self) -> dict:
        return {
            "宫名": self.gong_name,
            "方位": self.fangwei,
            "五行": self.wuxing,
            "地盘干": self.dipan_gan,
            "天盘干": self.tianpan_gan,
            "九星": self.jiuxing,
            "八门": self.bamen,
            "八神": self.bashen,
            "空亡": self.is_kong,
            "门迫": self.men_po,
            "反吟": self.fan_yin,
            "伏吟": self.fu_yin,
            "格局": self.geju,
            **({"备注": self.beizhu} if self.beizhu else {}),
        }


@dataclass
class PanResult:
    """完整排盘结果"""
    input_time: datetime
    sizhu: Sizhu
    jushu: Jushu
    xunshou: Xunshou
    zhifu_zhishi: ZhifuZhishi
    gongs: dict[int, GongData]

    # 元信息
    engine_version: str = "1.0.0"
    generated_at: str = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> dict:
        return {
            "meta": {
                "engine": "qimen-core",
                "version": self.engine_version,
                "input_time": self.input_time.isoformat(),
                "generated_at": self.generated_at,
            },
            "sizhu": self.sizhu.to_dict(),
            "jushu": self.jushu.to_dict(),
            "xunshou": self.xunshou.to_dict(),
            "zhifu_zhishi": self.zhifu_zhishi.to_dict(),
            "gongs": {str(k): v.to_dict() for k, v in self.gongs.items()},
        }

    def to_json(self, indent: int = 2) -> str:
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
