# 微信适配器（可选）

这个目录只放**补丁和说明**，不放第三方二进制、密钥或数据库。

## 里面有什么

```text
tools/wechat/
├── README.md
└── patches/
    └── wechat-cli-moments.patch   # 给 wechat-cli 加 moments 子命令
```

- 上游：`https://github.com/huohuoer/wechat-cli`（Apache-2.0）
- 固定 commit：`a378923`
- 补丁 SHA-256：`4db0bcaae28d2332c28f9d508fd997d0ee18a8f4cddb7fc773c544c746fa05f6`
- 解析逻辑参考：`chatlog-plus/moments.py`（MIT）

## 装法

```bash
python scripts/wechat_install.py --method wechat-cli-moments --dry-run
python scripts/wechat_install.py --method wechat-cli-moments --yes
wechat-cli init
```

## 为什么不在仓库里放二进制

- 体积、更新、杀毒软件、供应链风险都由第三方工具承担；
- 许可证和合规状态需要单独说明；
- 按需下载、固定版本、校验补丁，比捆一个 exe 更容易审计。

## 平台

| 平台 | 状态 |
|---|---|
| Windows 10/11 | 已实测（微信 4.1.15.53） |
| macOS Apple Silicon | 大概率可用，需实测；需 sudo / 完全磁盘访问 |
| macOS Intel | 暂不作为承诺：仓库只有 arm64 取钥二进制 |
| Linux | 未验证；需 root |

补丁本身是纯 Python，平台无关；真正卡点在取钥。取不到 `sns.db` 的 key 时，`moments` 会明确报错。

## 许可

- `wechat-cli`：Apache-2.0；
- `chatlog-plus/moments.py`：MIT；
- 本补丁：随本仓库发布，保留上游署名和许可证。
