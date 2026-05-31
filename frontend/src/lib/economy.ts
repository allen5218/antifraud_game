/** 強制清算時，房產變賣的回收比例 */
// IMPORTANT: must stay in sync with backend/app/economy/service.py LIQUIDATION_RATIO.
// This is duplicated because constants are not carried by the generated OpenAPI client.
export const LIQUIDATION_RATIO = 0.6
