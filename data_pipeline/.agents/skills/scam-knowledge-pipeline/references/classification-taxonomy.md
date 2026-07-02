# Classification Taxonomy

Codex classifies every validated fetched record into one primary `taxonomy_code`.

## Required Codes

| Code | Label | Typical signals |
|---|---|---|
| `investment_fraud` | 投資詐欺 | 假投資, 投資群組, 保證獲利, 出金, 虛擬貨幣, 博弈, 股票老師, 投顧 |
| `fake_online_auction_purchase` | 假網路拍賣（購物） | 拍賣平台, 賣貨便, 蝦皮, 露天, 商品頁, 假買家, 假賣家, 下標 |
| `general_purchase_fraud` | 一般購物詐欺（偽稱買賣） | 買賣, 商品, 貨款, 私下交易, 未出貨, 貨到付款, 代購 |
| `romance_fraud` | 假愛情交友 | 交友, 感情, 戀愛, 見面, 伴侶, 軍醫, 外國人, 感情誘導 |
| `atm_installment_cancellation_fraud` | 解除分期付款詐欺（ATM） | 解除分期, 分期付款, ATM, 操作提款機, 假客服, 誤設分期, 驗證金 |

## Agent Classification Protocol

For each fetched record:

1. Preserve Traditional Chinese text.
2. Read source taxonomy and matched keywords.
3. Choose one primary `taxonomy_code`.
4. Fill `category_evidence` with only evidence supported by source text.
5. Include `evidence_quotes` copied from source text.
6. Set `classification_confidence` from 0 to 1.
7. Use `classification_notes` for ambiguity.

Do not invent missing dates, actors, amounts, platforms, or payment methods. Use empty arrays or nulls.
