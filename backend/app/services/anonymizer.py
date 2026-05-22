import re
import hashlib
from typing import Optional


class Anonymizer:
    """Local anonymization engine. Replaces PII before any data leaves the machine."""

    # Unicode range for CJK characters (Chinese characters)
    CJK = r'一-鿿㐀-䶿'

    # Common Chinese surname + given name pattern (2-4 Chinese chars)
    CHINESE_NAME_PATTERN = re.compile(
        rf'(?:[王李张刘陈杨黄赵周吴徐孙马胡朱郭何罗高林郑梁谢唐许冯宋韩邓彭曹曾田董萧潘袁蔡沈于叶蒋苏魏吕薛丁杜钟汪贾谭石崔程廖姚方金邱夏韦邹石熊孟秦阎薛侯龙万段雷钱汤尹易常武乔贺赖龚文][{CJK}]{{1,2}})'
    )

    NAME_REPLACEMENTS: dict[str, str] = {}

    PHONE_PATTERN = re.compile(r'(?:\+?86)?1[3-9]\d{9}')
    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    ID_CARD_PATTERN = re.compile(r'\d{17}[\dXx]')

    # Common Chinese cities/locations (2-4 chars)
    LOCATION_PATTERN = re.compile(
        rf'(?:[{CJK}]{{2,4}}(?:市|省|区|县|镇|村|路|街|巷|道|广场|大厦|中心|小区|花园|酒店|饭店|餐厅|咖啡|茶|酒吧|商场|超市|医院|学校|大学|学院|公园|景区|机场|火车站|地铁站|公交站))'
    )

    # Common company suffixes
    ORG_PATTERN = re.compile(
        rf'(?:[{CJK}]{{2,6}}(?:公司|集团|科技|技术|网络|信息|数据|软件|电商|金融|投资|银行|保险|证券|基金|传媒|文化|娱乐|影视|音乐|游戏|教育|医疗|健康|物流|快递|出行|旅游|酒店|餐饮|房地产|物业|建筑|装修|汽车|能源|环保|农业|食品|服装|美妆|日化|家电|数码|通讯|互联网|云计算|大数据|人工智能|区块链|物联网|科技|有限|股份))'
    )

    def __init__(self):
        self._name_counter = 0
        self._loc_counter = 0
        self._org_counter = 0
        self._phone_counter = 0
        self._email_counter = 0

    def anonymize(self, text: str, sender: str) -> tuple[str, str]:
        """Anonymize text and sender name. Returns (anonymized_text, anonymized_sender)."""
        anon_sender = self._anonymize_name(sender)
        anon_text = text

        # Anonymize locations
        anon_text = self._replace_with_counter(self.LOCATION_PATTERN, anon_text, "LOCATION_", self._loc_counter)
        self._loc_counter += 1

        # Anonymize organizations
        anon_text = self._replace_with_counter(self.ORG_PATTERN, anon_text, "ORG_", self._org_counter)
        self._org_counter += 1

        # Anonymize names in text
        anon_text = self._replace_with_counter(self.CHINESE_NAME_PATTERN, anon_text, "PERSON_", 0)

        # Anonymize phone numbers
        anon_text = self.PHONE_PATTERN.sub(
            lambda m: self._get_phone_replacement(m.group()), anon_text
        )
        # Anonymize email addresses
        anon_text = self.EMAIL_PATTERN.sub(
            lambda m: self._get_email_replacement(m.group()), anon_text
        )

        return anon_text, anon_sender

    def _anonymize_name(self, name: str) -> str:
        if name in self.NAME_REPLACEMENTS:
            return self.NAME_REPLACEMENTS[name]

        if name == "SYSTEM":
            return "SYSTEM"

        self._name_counter += 1
        anon = f"USER_{chr(64 + self._name_counter)}" if self._name_counter <= 26 else f"USER_{self._name_counter}"
        self.NAME_REPLACEMENTS[name] = anon
        return anon

    def _replace_with_counter(self, pattern: re.Pattern, text: str, prefix: str, counter: int) -> str:
        result = text
        matches = pattern.findall(text)
        for i, match in enumerate(matches):
            if isinstance(match, tuple):
                match = match[0]
            result = result.replace(match, f"{prefix}{counter + i + 1}", 1)
        return result

    def _get_phone_replacement(self, phone: str) -> str:
        key = hashlib.md5(phone.encode()).hexdigest()[:6]
        return f"PHONE_{key}"

    def _get_email_replacement(self, email: str) -> str:
        key = hashlib.md5(email.encode()).hexdigest()[:6]
        return f"EMAIL_{key}"
