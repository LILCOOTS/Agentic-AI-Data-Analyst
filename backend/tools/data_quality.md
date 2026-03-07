# Data Quality Checks

A reference guide for the deterministic data quality checks performed before LLM involvement.

---

## 1️⃣ High Missing Value Columns

| Missing % | Recommendation |
|-----------|---------------|
| > 80%     | Recommend **dropping** the column |
| 20% – 80% | Recommend **imputation** |
| < 5%      | Low concern |

**Example detection output:**
```json
{
  "high_missing_columns": ["Alley", "PoolQC", "MiscFeature"],
  "moderate_missing_columns": ["LotFrontage", "MasVnrType"],
  "low_missing_columns": ["Electrical"]
}
```

> [!NOTE]
> Many models perform poorly with large missing sections. Features with >90% missing values rarely carry useful signal.

---

## 2️⃣ ID-Like Columns

**Rule:** If `unique_count == num_rows`, the column is likely an identifier and should be **excluded from modelling**.

**Example detection output:**
```json
{
  "id_like_columns": ["Id"]
}
```

---

## 3️⃣ High Skew Numerical Features

**Rule:** `|skewness| > 2`

**Examples from dataset:** `LotArea`, `MiscVal`, `PoolArea`

**Example detection output:**
```json
{
  "high_skew_columns": ["LotArea", "MiscVal", "PoolArea"]
}
```

**Suggested transformations:**
- Log transform
- Box-Cox transform

---

## 4️⃣ Low Variance Columns

**Rule:** `unique_count == 1` or `unique_count / num_rows < 0.01`

These features add almost no predictive power.

**Example detection output:**
```json
{
  "low_variance_columns": []
}
```

---

## 5️⃣ Potential Target Candidates

Deterministic detection can suggest target candidates even before LLM involvement.

| Task Type | Rule |
|-----------|------|
| Classification | `2 <= unique_count <= 10` |
| Regression | Numerical column with large variance |

**Example from dataset:** `SalePrice`

**Example detection output:**
```json
{
  "candidate_targets": ["SalePrice"]
}
```

> [!NOTE]
> The LLM will later verify the semantic meaning of suggested targets.

---

## 6️⃣ Mixed Data Type Columns

Sometimes columns contain a mix of numeric and string values (e.g., `"123"`, `"abc"`, `456`).

**Rule:** Attempt numeric conversion and detect failures.

**Example detection output:**
```json
{
  "mixed_type_columns": []
}
```

> [!IMPORTANT]
> Mixed-type columns require cleaning before use.

---

## 7️⃣ High Cardinality Categorical Features

**Rule:** `unique_count > 50`

These columns often need special encoding:
- Target encoding
- Hashing
- Embedding

**Example detection output:**
```json
{
  "high_cardinality_columns": []
}
```