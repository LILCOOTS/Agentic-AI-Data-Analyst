the responses are without the EDA graph result on purpose as it would be useless for now

/get\_full\_analysis : before cleaning response:-
---



{

&nbsp; "selected\_columns": {

&nbsp;   "numerical\_columns": \[

&nbsp;     "LotArea",

&nbsp;     "GrLivArea",

&nbsp;     "MiscVal",

&nbsp;     "BsmtFinSF1"

&nbsp;   ],

&nbsp;   "categorical\_columns": \[

&nbsp;     "MSZoning",

&nbsp;     "LotShape",

&nbsp;     "LandContour",

&nbsp;     "LotConfig",

&nbsp;     "LandSlope"

&nbsp;   ],

&nbsp;   "target\_column": "SalePrice",

&nbsp;   "problem\_type": "regression",

&nbsp;   "correlation\_pairs": \[

&nbsp;     \[

&nbsp;       "LotArea",

&nbsp;       "GrLivArea"

&nbsp;     ],

&nbsp;     \[

&nbsp;       "LotArea",

&nbsp;       "BsmtFinSF1"

&nbsp;     ],

&nbsp;     \[

&nbsp;       "GrLivArea",

&nbsp;       "BsmtFinSF1"

&nbsp;     ]

&nbsp;   ],

&nbsp;   "skewed\_columns": \[

&nbsp;     "LotArea",

&nbsp;     "MiscVal"

&nbsp;   ]

&nbsp; },

&nbsp; "insights": {

&nbsp;   "general": {

&nbsp;     "summary": "The dataset has 1,460 rows and 81 columns (38 numerical, 43 categorical). 'SalePrice' is identified as the target variable for regression. 5 column(s) have >50% missing values and are candidates for removal. 13 numerical feature(s) are highly skewed — log transformation is recommended.",

&nbsp;     "missing": \[

&nbsp;       "'Alley' has 93.8% missing — recommended to drop.",

&nbsp;       "'MasVnrType' has 59.7% missing — recommended to drop.",

&nbsp;       "'PoolQC' has 99.5% missing — recommended to drop.",

&nbsp;       "'Fence' has 80.8% missing — recommended to drop.",

&nbsp;       "'MiscFeature' has 96.3% missing — recommended to drop.",

&nbsp;       "'LotFrontage' has 17.7% missing — consider imputation.",

&nbsp;       "'BsmtQual' has 2.5% missing — consider imputation.",

&nbsp;       "'BsmtCond' has 2.5% missing — consider imputation.",

&nbsp;       "'BsmtExposure' has 2.6% missing — consider imputation.",

&nbsp;       "'BsmtFinType1' has 2.5% missing — consider imputation.",

&nbsp;       "'BsmtFinType2' has 2.6% missing — consider imputation.",

&nbsp;       "'FireplaceQu' has 47.3% missing — consider imputation.",

&nbsp;       "'GarageType' has 5.5% missing — consider imputation.",

&nbsp;       "'GarageYrBlt' has 5.5% missing — consider imputation.",

&nbsp;       "'GarageFinish' has 5.5% missing — consider imputation.",

&nbsp;       "'GarageQual' has 5.5% missing — consider imputation.",

&nbsp;       "'GarageCond' has 5.5% missing — consider imputation."

&nbsp;     ],

&nbsp;     "skewness": \[

&nbsp;       "'LotArea' is highly skewed (skewness = 12.21) — log1p transformation will stabilise variance and reduce model bias.",

&nbsp;       "'MiscVal' is highly skewed (skewness = 24.48) — log1p transformation will stabilise variance and reduce model bias."

&nbsp;     ],

&nbsp;     "correlation": \[],

&nbsp;     "target": "'SalePrice' is the regression target (selected from candidate targets)."

&nbsp;   },

&nbsp;   "key\_findings": \[

&nbsp;     "'GrLivArea' is very strongly correlated positively with 'SalePrice' (r = 0.71), indicating high predictive importance.",

&nbsp;     "'BsmtFinSF1' is moderately correlated positively with 'SalePrice' (r = 0.39), indicating limited predictive importance.",

&nbsp;     "'LotArea' is moderately correlated positively with 'SalePrice' (r = 0.26), indicating limited predictive importance."

&nbsp;   ],

&nbsp;   "feature\_importance": \[

&nbsp;     {

&nbsp;       "feature": "GrLivArea",

&nbsp;       "correlation": 0.709

&nbsp;     },

&nbsp;     {

&nbsp;       "feature": "BsmtFinSF1",

&nbsp;       "correlation": 0.386

&nbsp;     },

&nbsp;     {

&nbsp;       "feature": "LotArea",

&nbsp;       "correlation": 0.264

&nbsp;     },

&nbsp;     {

&nbsp;       "feature": "MiscVal",

&nbsp;       "correlation": -0.021

&nbsp;     }

&nbsp;   ],

&nbsp;   "correlation": \[],

&nbsp;   "target\_analysis": \[

&nbsp;     "'GrLivArea' is positively related to 'SalePrice' (r = 0.71) — very strong signal.",

&nbsp;     "'BsmtFinSF1' is positively related to 'SalePrice' (r = 0.39) — moderate signal.",

&nbsp;     "'LotArea' is positively related to 'SalePrice' (r = 0.26) — moderate signal.",

&nbsp;     "'SalePrice' varies across 'MSZoning': avg 214,014.1 for 'FV' vs 74,528.0 for 'C (all)' — this categorical split is predictive.",

&nbsp;     "'SalePrice' varies across 'LotShape': avg 239,833.4 for 'IR2' vs 164,754.8 for 'Reg' — this categorical split is predictive.",

&nbsp;     "'SalePrice' varies across 'LandContour': avg 231,533.9 for 'HLS' vs 143,104.1 for 'Bnk' — this categorical split is predictive."

&nbsp;   ],

&nbsp;   "risk\_flags": \[

&nbsp;     "High missing values detected in: 'Alley', 'MasVnrType', 'PoolQC', 'Fence', 'MiscFeature'.",

&nbsp;     "Highly skewed features: 'LotFrontage', 'LotArea', 'MasVnrArea', 'BsmtFinSF2', 'LowQualFinSF', 'BsmtHalfBath', 'KitchenAbvGr', 'OpenPorchSF', 'EnclosedPorch', '3SsnPorch', 'ScreenPorch', 'PoolArea', 'MiscVal' — may distort distance-based and linear models.",

&nbsp;     "ID-like columns detected ('Id') — must be excluded from training."

&nbsp;   ],

&nbsp;   "recommendations": \[

&nbsp;     "Drop 'Alley' — 93.8% of values are missing, making it unreliable for modelling.",

&nbsp;     "Drop 'MasVnrType' — 59.7% of values are missing, making it unreliable for modelling.",

&nbsp;     "Drop 'PoolQC' — 99.5% of values are missing, making it unreliable for modelling.",

&nbsp;     "Drop 'Fence' — 80.8% of values are missing, making it unreliable for modelling.",

&nbsp;     "Drop 'MiscFeature' — 96.3% of values are missing, making it unreliable for modelling."

&nbsp;   ],

&nbsp;   "llm": "Error code: 413 - {'error': {'message': 'Request too large for model `openai/gpt-oss-120b` in organization `org\_01kfjgf3pge6qvqxwrsh23sg7w` service tier `on\_demand` on tokens per minute (TPM): Limit 8000, Requested 8249, please reduce your message size and try again. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing', 'type': 'tokens', 'code': 'rate\_limit\_exceeded'}}"

&nbsp; }

}



### /cleaning: response



{

&nbsp; "session\_id": "1a76df98-425b-4436-83af-1f063519e769",

&nbsp; "rows\_before": 1460,

&nbsp; "rows\_after": 1460,

&nbsp; "columns\_before": 81,

&nbsp; "columns\_after": 75,

&nbsp; "cleaning\_log": \[

&nbsp;   {

&nbsp;     "column": "Alley",

&nbsp;     "action": "drop\_column",

&nbsp;     "status": "done"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "MasVnrType",

&nbsp;     "action": "drop\_column",

&nbsp;     "status": "done"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "PoolQC",

&nbsp;     "action": "drop\_column",

&nbsp;     "status": "done"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "Fence",

&nbsp;     "action": "drop\_column",

&nbsp;     "status": "done"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "MiscFeature",

&nbsp;     "action": "drop\_column",

&nbsp;     "status": "done"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "Id",

&nbsp;     "action": "drop\_column",

&nbsp;     "status": "done"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "LotFrontage",

&nbsp;     "action": "impute\_with\_median",

&nbsp;     "status": "filled 259 nulls"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "BsmtQual",

&nbsp;     "action": "fill\_with\_none",

&nbsp;     "status": "filled 37 NaNs with 'None'"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "BsmtCond",

&nbsp;     "action": "fill\_with\_none",

&nbsp;     "status": "filled 37 NaNs with 'None'"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "BsmtExposure",

&nbsp;     "action": "fill\_with\_none",

&nbsp;     "status": "filled 38 NaNs with 'None'"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "BsmtFinType1",

&nbsp;     "action": "fill\_with\_none",

&nbsp;     "status": "filled 37 NaNs with 'None'"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "BsmtFinType2",

&nbsp;     "action": "fill\_with\_none",

&nbsp;     "status": "filled 38 NaNs with 'None'"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "FireplaceQu",

&nbsp;     "action": "fill\_with\_none",

&nbsp;     "status": "filled 690 NaNs with 'None'"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "GarageType",

&nbsp;     "action": "fill\_with\_none",

&nbsp;     "status": "filled 81 NaNs with 'None'"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "GarageYrBlt",

&nbsp;     "action": "impute\_with\_mean",

&nbsp;     "status": "filled 81 nulls"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "GarageFinish",

&nbsp;     "action": "fill\_with\_none",

&nbsp;     "status": "filled 81 NaNs with 'None'"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "GarageQual",

&nbsp;     "action": "fill\_with\_none",

&nbsp;     "status": "filled 81 NaNs with 'None'"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "GarageCond",

&nbsp;     "action": "fill\_with\_none",

&nbsp;     "status": "filled 81 NaNs with 'None'"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": null,

&nbsp;     "action": "drop\_duplicates",

&nbsp;     "status": "removed 0 duplicate rows"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "LotFrontage",

&nbsp;     "action": "transform",

&nbsp;     "status": "log1p applied"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "LotArea",

&nbsp;     "action": "transform",

&nbsp;     "status": "log1p applied"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "MasVnrArea",

&nbsp;     "action": "add\_binary\_indicator",

&nbsp;     "status": "created 'MasVnrArea\_present' (0/1), dropped original"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "BsmtFinSF2",

&nbsp;     "action": "add\_binary\_indicator",

&nbsp;     "status": "created 'BsmtFinSF2\_present' (0/1), dropped original"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "LowQualFinSF",

&nbsp;     "action": "add\_binary\_indicator",

&nbsp;     "status": "created 'LowQualFinSF\_present' (0/1), dropped original"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "BsmtHalfBath",

&nbsp;     "action": "add\_binary\_indicator",

&nbsp;     "status": "created 'BsmtHalfBath\_present' (0/1), dropped original"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "KitchenAbvGr",

&nbsp;     "action": "transform",

&nbsp;     "status": "log1p applied"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "OpenPorchSF",

&nbsp;     "action": "transform",

&nbsp;     "status": "log1p applied"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "EnclosedPorch",

&nbsp;     "action": "add\_binary\_indicator",

&nbsp;     "status": "created 'EnclosedPorch\_present' (0/1), dropped original"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "3SsnPorch",

&nbsp;     "action": "add\_binary\_indicator",

&nbsp;     "status": "created '3SsnPorch\_present' (0/1), dropped original"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "ScreenPorch",

&nbsp;     "action": "add\_binary\_indicator",

&nbsp;     "status": "created 'ScreenPorch\_present' (0/1), dropped original"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "PoolArea",

&nbsp;     "action": "add\_binary\_indicator",

&nbsp;     "status": "created 'PoolArea\_present' (0/1), dropped original"

&nbsp;   },

&nbsp;   {

&nbsp;     "column": "MiscVal",

&nbsp;     "action": "add\_binary\_indicator",

&nbsp;     "status": "created 'MiscVal\_present' (0/1), dropped original"

&nbsp;   }

&nbsp; ],

&nbsp; "actions\_applied": 32,

&nbsp; "metadata": {

&nbsp;   "num\_rows": 1460,

&nbsp;   "num\_columns": 75,

&nbsp;   "columns": \[

&nbsp;     "MSSubClass",

&nbsp;     "MSZoning",

&nbsp;     "LotFrontage",

&nbsp;     "LotArea",

&nbsp;     "Street",

&nbsp;     "LotShape",

&nbsp;     "LandContour",

&nbsp;     "Utilities",

&nbsp;     "LotConfig",

&nbsp;     "LandSlope",

&nbsp;     "Neighborhood",

&nbsp;     "Condition1",

&nbsp;     "Condition2",

&nbsp;     "BldgType",

&nbsp;     "HouseStyle",

&nbsp;     "OverallQual",

&nbsp;     "OverallCond",

&nbsp;     "YearBuilt",

&nbsp;     "YearRemodAdd",

&nbsp;     "RoofStyle",

&nbsp;     "RoofMatl",

&nbsp;     "Exterior1st",

&nbsp;     "Exterior2nd",

&nbsp;     "ExterQual",

&nbsp;     "ExterCond",

&nbsp;     "Foundation",

&nbsp;     "BsmtQual",

&nbsp;     "BsmtCond",

&nbsp;     "BsmtExposure",

&nbsp;     "BsmtFinType1",

&nbsp;     "BsmtFinSF1",

&nbsp;     "BsmtFinType2",

&nbsp;     "BsmtUnfSF",

&nbsp;     "TotalBsmtSF",

&nbsp;     "Heating",

&nbsp;     "HeatingQC",

&nbsp;     "CentralAir",

&nbsp;     "Electrical",

&nbsp;     "1stFlrSF",

&nbsp;     "2ndFlrSF",

&nbsp;     "GrLivArea",

&nbsp;     "BsmtFullBath",

&nbsp;     "FullBath",

&nbsp;     "HalfBath",

&nbsp;     "BedroomAbvGr",

&nbsp;     "KitchenAbvGr",

&nbsp;     "KitchenQual",

&nbsp;     "TotRmsAbvGrd",

&nbsp;     "Functional",

&nbsp;     "Fireplaces",

&nbsp;     "FireplaceQu",

&nbsp;     "GarageType",

&nbsp;     "GarageYrBlt",

&nbsp;     "GarageFinish",

&nbsp;     "GarageCars",

&nbsp;     "GarageArea",

&nbsp;     "GarageQual",

&nbsp;     "GarageCond",

&nbsp;     "PavedDrive",

&nbsp;     "WoodDeckSF",

&nbsp;     "OpenPorchSF",

&nbsp;     "MoSold",

&nbsp;     "YrSold",

&nbsp;     "SaleType",

&nbsp;     "SaleCondition",

&nbsp;     "SalePrice",

&nbsp;     "MasVnrArea\_present",

&nbsp;     "BsmtFinSF2\_present",

&nbsp;     "LowQualFinSF\_present",

&nbsp;     "BsmtHalfBath\_present",

&nbsp;     "EnclosedPorch\_present",

&nbsp;     "3SsnPorch\_present",

&nbsp;     "ScreenPorch\_present",

&nbsp;     "PoolArea\_present",

&nbsp;     "MiscVal\_present"

&nbsp;   ],

&nbsp;   "column\_types": {

&nbsp;     "numerical": \[

&nbsp;       "MSSubClass",

&nbsp;       "LotFrontage",

&nbsp;       "LotArea",

&nbsp;       "OverallQual",

&nbsp;       "OverallCond",

&nbsp;       "YearBuilt",

&nbsp;       "YearRemodAdd",

&nbsp;       "BsmtFinSF1",

&nbsp;       "BsmtUnfSF",

&nbsp;       "TotalBsmtSF",

&nbsp;       "1stFlrSF",

&nbsp;       "2ndFlrSF",

&nbsp;       "GrLivArea",

&nbsp;       "BsmtFullBath",

&nbsp;       "FullBath",

&nbsp;       "HalfBath",

&nbsp;       "BedroomAbvGr",

&nbsp;       "KitchenAbvGr",

&nbsp;       "TotRmsAbvGrd",

&nbsp;       "Fireplaces",

&nbsp;       "GarageYrBlt",

&nbsp;       "GarageCars",

&nbsp;       "GarageArea",

&nbsp;       "WoodDeckSF",

&nbsp;       "OpenPorchSF",

&nbsp;       "MoSold",

&nbsp;       "YrSold",

&nbsp;       "SalePrice",

&nbsp;       "MasVnrArea\_present",

&nbsp;       "BsmtFinSF2\_present",

&nbsp;       "LowQualFinSF\_present",

&nbsp;       "BsmtHalfBath\_present",

&nbsp;       "EnclosedPorch\_present",

&nbsp;       "3SsnPorch\_present",

&nbsp;       "ScreenPorch\_present",

&nbsp;       "PoolArea\_present",

&nbsp;       "MiscVal\_present"

&nbsp;     ],

&nbsp;     "categorical": \[

&nbsp;       "MSZoning",

&nbsp;       "Street",

&nbsp;       "LotShape",

&nbsp;       "LandContour",

&nbsp;       "Utilities",

&nbsp;       "LotConfig",

&nbsp;       "LandSlope",

&nbsp;       "Neighborhood",

&nbsp;       "Condition1",

&nbsp;       "Condition2",

&nbsp;       "BldgType",

&nbsp;       "HouseStyle",

&nbsp;       "RoofStyle",

&nbsp;       "RoofMatl",

&nbsp;       "Exterior1st",

&nbsp;       "Exterior2nd",

&nbsp;       "ExterQual",

&nbsp;       "ExterCond",

&nbsp;       "Foundation",

&nbsp;       "BsmtQual",

&nbsp;       "BsmtCond",

&nbsp;       "BsmtExposure",

&nbsp;       "BsmtFinType1",

&nbsp;       "BsmtFinType2",

&nbsp;       "Heating",

&nbsp;       "HeatingQC",

&nbsp;       "CentralAir",

&nbsp;       "Electrical",

&nbsp;       "KitchenQual",

&nbsp;       "Functional",

&nbsp;       "FireplaceQu",

&nbsp;       "GarageType",

&nbsp;       "GarageFinish",

&nbsp;       "GarageQual",

&nbsp;       "GarageCond",

&nbsp;       "PavedDrive",

&nbsp;       "SaleType",

&nbsp;       "SaleCondition"

&nbsp;     ],

&nbsp;     "datetime": \[],

&nbsp;     "boolean": \[],

&nbsp;     "text": \[]

&nbsp;   },

&nbsp;   "missing\_summary": {

&nbsp;     "total\_missing": 1,

&nbsp;     "per\_column": {

&nbsp;       "MSSubClass": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "MSZoning": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "LotFrontage": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "LotArea": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "Street": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "LotShape": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "LandContour": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "Utilities": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "LotConfig": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "LandSlope": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "Neighborhood": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "Condition1": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "Condition2": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "BldgType": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "HouseStyle": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "OverallQual": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "OverallCond": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "YearBuilt": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "YearRemodAdd": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "RoofStyle": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "RoofMatl": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "Exterior1st": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "Exterior2nd": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "ExterQual": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "ExterCond": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "Foundation": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "BsmtQual": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "BsmtCond": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "BsmtExposure": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "BsmtFinType1": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "BsmtFinSF1": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "BsmtFinType2": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "BsmtUnfSF": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "TotalBsmtSF": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "Heating": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "HeatingQC": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "CentralAir": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "Electrical": {

&nbsp;         "missing\_count": 1,

&nbsp;         "missing\_percentage": 0.07

&nbsp;       },

&nbsp;       "1stFlrSF": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "2ndFlrSF": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "GrLivArea": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "BsmtFullBath": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "FullBath": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "HalfBath": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "BedroomAbvGr": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "KitchenAbvGr": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "KitchenQual": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "TotRmsAbvGrd": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "Functional": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "Fireplaces": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "FireplaceQu": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "GarageType": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "GarageYrBlt": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "GarageFinish": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "GarageCars": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "GarageArea": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "GarageQual": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "GarageCond": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "PavedDrive": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "WoodDeckSF": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "OpenPorchSF": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "MoSold": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "YrSold": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "SaleType": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "SaleCondition": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "SalePrice": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "MasVnrArea\_present": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "BsmtFinSF2\_present": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "LowQualFinSF\_present": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "BsmtHalfBath\_present": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "EnclosedPorch\_present": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "3SsnPorch\_present": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "ScreenPorch\_present": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "PoolArea\_present": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       },

&nbsp;       "MiscVal\_present": {

&nbsp;         "missing\_count": 0,

&nbsp;         "missing\_percentage": 0

&nbsp;       }

&nbsp;     }

&nbsp;   },

&nbsp;   "unique\_counts": {

&nbsp;     "MSSubClass": 15,

&nbsp;     "MSZoning": 5,

&nbsp;     "LotFrontage": 110,

&nbsp;     "LotArea": 1073,

&nbsp;     "Street": 2,

&nbsp;     "LotShape": 4,

&nbsp;     "LandContour": 4,

&nbsp;     "Utilities": 2,

&nbsp;     "LotConfig": 5,

&nbsp;     "LandSlope": 3,

&nbsp;     "Neighborhood": 25,

&nbsp;     "Condition1": 9,

&nbsp;     "Condition2": 8,

&nbsp;     "BldgType": 5,

&nbsp;     "HouseStyle": 8,

&nbsp;     "OverallQual": 10,

&nbsp;     "OverallCond": 9,

&nbsp;     "YearBuilt": 112,

&nbsp;     "YearRemodAdd": 61,

&nbsp;     "RoofStyle": 6,

&nbsp;     "RoofMatl": 8,

&nbsp;     "Exterior1st": 15,

&nbsp;     "Exterior2nd": 16,

&nbsp;     "ExterQual": 4,

&nbsp;     "ExterCond": 5,

&nbsp;     "Foundation": 6,

&nbsp;     "BsmtQual": 5,

&nbsp;     "BsmtCond": 5,

&nbsp;     "BsmtExposure": 5,

&nbsp;     "BsmtFinType1": 7,

&nbsp;     "BsmtFinSF1": 637,

&nbsp;     "BsmtFinType2": 7,

&nbsp;     "BsmtUnfSF": 780,

&nbsp;     "TotalBsmtSF": 721,

&nbsp;     "Heating": 6,

&nbsp;     "HeatingQC": 5,

&nbsp;     "CentralAir": 2,

&nbsp;     "Electrical": 5,

&nbsp;     "1stFlrSF": 753,

&nbsp;     "2ndFlrSF": 417,

&nbsp;     "GrLivArea": 861,

&nbsp;     "BsmtFullBath": 4,

&nbsp;     "FullBath": 4,

&nbsp;     "HalfBath": 3,

&nbsp;     "BedroomAbvGr": 8,

&nbsp;     "KitchenAbvGr": 4,

&nbsp;     "KitchenQual": 4,

&nbsp;     "TotRmsAbvGrd": 12,

&nbsp;     "Functional": 7,

&nbsp;     "Fireplaces": 4,

&nbsp;     "FireplaceQu": 6,

&nbsp;     "GarageType": 7,

&nbsp;     "GarageYrBlt": 98,

&nbsp;     "GarageFinish": 4,

&nbsp;     "GarageCars": 5,

&nbsp;     "GarageArea": 441,

&nbsp;     "GarageQual": 6,

&nbsp;     "GarageCond": 6,

&nbsp;     "PavedDrive": 3,

&nbsp;     "WoodDeckSF": 274,

&nbsp;     "OpenPorchSF": 202,

&nbsp;     "MoSold": 12,

&nbsp;     "YrSold": 5,

&nbsp;     "SaleType": 9,

&nbsp;     "SaleCondition": 6,

&nbsp;     "SalePrice": 663,

&nbsp;     "MasVnrArea\_present": 2,

&nbsp;     "BsmtFinSF2\_present": 2,

&nbsp;     "LowQualFinSF\_present": 2,

&nbsp;     "BsmtHalfBath\_present": 2,

&nbsp;     "EnclosedPorch\_present": 2,

&nbsp;     "3SsnPorch\_present": 2,

&nbsp;     "ScreenPorch\_present": 2,

&nbsp;     "PoolArea\_present": 2,

&nbsp;     "MiscVal\_present": 2

&nbsp;   },

&nbsp;   "numerical\_summary": {

&nbsp;     "MSSubClass": {

&nbsp;       "mean": 56.897260273972606,

&nbsp;       "std": 42.300570993810425,

&nbsp;       "min": 20,

&nbsp;       "max": 190,

&nbsp;       "median": 50,

&nbsp;       "skewness": 1.4076567471495591

&nbsp;     },

&nbsp;     "LotFrontage": {

&nbsp;       "mean": 4.2144507580064525,

&nbsp;       "std": 0.3143950893565165,

&nbsp;       "min": 3.091042453358316,

&nbsp;       "max": 5.749392985908253,

&nbsp;       "median": 4.248495242049359,

&nbsp;       "skewness": -0.870005697584457

&nbsp;     },

&nbsp;     "LotArea": {

&nbsp;       "mean": 9.110966323939161,

&nbsp;       "std": 0.5173690129860723,

&nbsp;       "min": 7.170888478512505,

&nbsp;       "max": 12.279536839074337,

&nbsp;       "median": 9.156886838722746,

&nbsp;       "skewness": -0.13740448122837784

&nbsp;     },

&nbsp;     "OverallQual": {

&nbsp;       "mean": 6.0993150684931505,

&nbsp;       "std": 1.3829965467415934,

&nbsp;       "min": 1,

&nbsp;       "max": 10,

&nbsp;       "median": 6,

&nbsp;       "skewness": 0.2169439277628693

&nbsp;     },

&nbsp;     "OverallCond": {

&nbsp;       "mean": 5.575342465753424,

&nbsp;       "std": 1.1127993367127316,

&nbsp;       "min": 1,

&nbsp;       "max": 9,

&nbsp;       "median": 5,

&nbsp;       "skewness": 0.6930674724842182

&nbsp;     },

&nbsp;     "YearBuilt": {

&nbsp;       "mean": 1971.267808219178,

&nbsp;       "std": 30.202904042525258,

&nbsp;       "min": 1872,

&nbsp;       "max": 2010,

&nbsp;       "median": 1973,

&nbsp;       "skewness": -0.613461172488183

&nbsp;     },

&nbsp;     "YearRemodAdd": {

&nbsp;       "mean": 1984.8657534246574,

&nbsp;       "std": 20.645406807709413,

&nbsp;       "min": 1950,

&nbsp;       "max": 2010,

&nbsp;       "median": 1994,

&nbsp;       "skewness": -0.5035620027004709

&nbsp;     },

&nbsp;     "BsmtFinSF1": {

&nbsp;       "mean": 443.6397260273973,

&nbsp;       "std": 456.0980908409277,

&nbsp;       "min": 0,

&nbsp;       "max": 5644,

&nbsp;       "median": 383.5,

&nbsp;       "skewness": 1.685503071910789

&nbsp;     },

&nbsp;     "BsmtUnfSF": {

&nbsp;       "mean": 567.2404109589041,

&nbsp;       "std": 441.86695529243417,

&nbsp;       "min": 0,

&nbsp;       "max": 2336,

&nbsp;       "median": 477.5,

&nbsp;       "skewness": 0.9202684528039037

&nbsp;     },

&nbsp;     "TotalBsmtSF": {

&nbsp;       "mean": 1057.4294520547944,

&nbsp;       "std": 438.7053244594708,

&nbsp;       "min": 0,

&nbsp;       "max": 6110,

&nbsp;       "median": 991.5,

&nbsp;       "skewness": 1.5242545490627664

&nbsp;     },

&nbsp;     "1stFlrSF": {

&nbsp;       "mean": 1162.626712328767,

&nbsp;       "std": 386.5877380410744,

&nbsp;       "min": 334,

&nbsp;       "max": 4692,

&nbsp;       "median": 1087,

&nbsp;       "skewness": 1.3767566220336365

&nbsp;     },

&nbsp;     "2ndFlrSF": {

&nbsp;       "mean": 346.99246575342465,

&nbsp;       "std": 436.5284358862568,

&nbsp;       "min": 0,

&nbsp;       "max": 2065,

&nbsp;       "median": 0,

&nbsp;       "skewness": 0.8130298163023265

&nbsp;     },

&nbsp;     "GrLivArea": {

&nbsp;       "mean": 1515.463698630137,

&nbsp;       "std": 525.4803834232025,

&nbsp;       "min": 334,

&nbsp;       "max": 5642,

&nbsp;       "median": 1464,

&nbsp;       "skewness": 1.3665603560164552

&nbsp;     },

&nbsp;     "BsmtFullBath": {

&nbsp;       "mean": 0.42534246575342466,

&nbsp;       "std": 0.5189106060898065,

&nbsp;       "min": 0,

&nbsp;       "max": 3,

&nbsp;       "median": 0,

&nbsp;       "skewness": 0.596066609663168

&nbsp;     },

&nbsp;     "FullBath": {

&nbsp;       "mean": 1.5650684931506849,

&nbsp;       "std": 0.5509158012954317,

&nbsp;       "min": 0,

&nbsp;       "max": 3,

&nbsp;       "median": 2,

&nbsp;       "skewness": 0.036561558402727165

&nbsp;     },

&nbsp;     "HalfBath": {

&nbsp;       "mean": 0.38287671232876713,

&nbsp;       "std": 0.5028853810928914,

&nbsp;       "min": 0,

&nbsp;       "max": 2,

&nbsp;       "median": 0,

&nbsp;       "skewness": 0.675897448233722

&nbsp;     },

&nbsp;     "BedroomAbvGr": {

&nbsp;       "mean": 2.8664383561643834,

&nbsp;       "std": 0.8157780441442284,

&nbsp;       "min": 0,

&nbsp;       "max": 8,

&nbsp;       "median": 3,

&nbsp;       "skewness": 0.21179009627507137

&nbsp;     },

&nbsp;     "KitchenAbvGr": {

&nbsp;       "mean": 0.7116734676884321,

&nbsp;       "std": 0.08926775460278703,

&nbsp;       "min": 0,

&nbsp;       "max": 1.3862943611198906,

&nbsp;       "median": 0.6931471805599453,

&nbsp;       "skewness": 3.8694137036546494

&nbsp;     },

&nbsp;     "TotRmsAbvGrd": {

&nbsp;       "mean": 6.517808219178082,

&nbsp;       "std": 1.6253932905840505,

&nbsp;       "min": 2,

&nbsp;       "max": 14,

&nbsp;       "median": 6,

&nbsp;       "skewness": 0.6763408364355531

&nbsp;     },

&nbsp;     "Fireplaces": {

&nbsp;       "mean": 0.613013698630137,

&nbsp;       "std": 0.6446663863122295,

&nbsp;       "min": 0,

&nbsp;       "max": 3,

&nbsp;       "median": 1,

&nbsp;       "skewness": 0.6495651830548841

&nbsp;     },

&nbsp;     "GarageYrBlt": {

&nbsp;       "mean": 1978.5061638868744,

&nbsp;       "std": 23.994583259057606,

&nbsp;       "min": 1900,

&nbsp;       "max": 2010,

&nbsp;       "median": 1978.5061638868744,

&nbsp;       "skewness": -0.6681748227563908

&nbsp;     },

&nbsp;     "GarageCars": {

&nbsp;       "mean": 1.7671232876712328,

&nbsp;       "std": 0.7473150101111095,

&nbsp;       "min": 0,

&nbsp;       "max": 4,

&nbsp;       "median": 2,

&nbsp;       "skewness": -0.3425489297486655

&nbsp;     },

&nbsp;     "GarageArea": {

&nbsp;       "mean": 472.9801369863014,

&nbsp;       "std": 213.80484145338042,

&nbsp;       "min": 0,

&nbsp;       "max": 1418,

&nbsp;       "median": 480,

&nbsp;       "skewness": 0.17998090674623907

&nbsp;     },

&nbsp;     "WoodDeckSF": {

&nbsp;       "mean": 94.2445205479452,

&nbsp;       "std": 125.3387943517241,

&nbsp;       "min": 0,

&nbsp;       "max": 857,

&nbsp;       "median": 0,

&nbsp;       "skewness": 1.5413757571931312

&nbsp;     },

&nbsp;     "OpenPorchSF": {

&nbsp;       "mean": 2.3085408330706905,

&nbsp;       "std": 2.1523873381539835,

&nbsp;       "min": 0,

&nbsp;       "max": 6.306275286948016,

&nbsp;       "median": 3.258096538021482,

&nbsp;       "skewness": -0.02339729485739231

&nbsp;     },

&nbsp;     "MoSold": {

&nbsp;       "mean": 6.321917808219178,

&nbsp;       "std": 2.7036262083595126,

&nbsp;       "min": 1,

&nbsp;       "max": 12,

&nbsp;       "median": 6,

&nbsp;       "skewness": 0.21205298505146022

&nbsp;     },

&nbsp;     "YrSold": {

&nbsp;       "mean": 2007.8157534246575,

&nbsp;       "std": 1.3280951205521099,

&nbsp;       "min": 2006,

&nbsp;       "max": 2010,

&nbsp;       "median": 2008,

&nbsp;       "skewness": 0.09626851386568028

&nbsp;     },

&nbsp;     "SalePrice": {

&nbsp;       "mean": 180921.19589041095,

&nbsp;       "std": 79442.50288288662,

&nbsp;       "min": 34900,

&nbsp;       "max": 755000,

&nbsp;       "median": 163000,

&nbsp;       "skewness": 1.8828757597682129

&nbsp;     },

&nbsp;     "MasVnrArea\_present": {

&nbsp;       "mean": 0.4047945205479452,

&nbsp;       "std": 0.4910204215618646,

&nbsp;       "min": 0,

&nbsp;       "max": 1,

&nbsp;       "median": 0,

&nbsp;       "skewness": 0.38831817428003573

&nbsp;     },

&nbsp;     "BsmtFinSF2\_present": {

&nbsp;       "mean": 0.11438356164383562,

&nbsp;       "std": 0.31838560514097775,

&nbsp;       "min": 0,

&nbsp;       "max": 1,

&nbsp;       "median": 0,

&nbsp;       "skewness": 2.425646124880188

&nbsp;     },

&nbsp;     "LowQualFinSF\_present": {

&nbsp;       "mean": 0.01780821917808219,

&nbsp;       "std": 0.13229918713001904,

&nbsp;       "min": 0,

&nbsp;       "max": 1,

&nbsp;       "median": 0,

&nbsp;       "skewness": 7.299413308101928

&nbsp;     },

&nbsp;     "BsmtHalfBath\_present": {

&nbsp;       "mean": 0.056164383561643834,

&nbsp;       "std": 0.230317777534327,

&nbsp;       "min": 0,

&nbsp;       "max": 1,

&nbsp;       "median": 0,

&nbsp;       "skewness": 3.859401989741791

&nbsp;     },

&nbsp;     "EnclosedPorch\_present": {

&nbsp;       "mean": 0.14246575342465753,

&nbsp;       "std": 0.34964696117021565,

&nbsp;       "min": 0,

&nbsp;       "max": 1,

&nbsp;       "median": 0,

&nbsp;       "skewness": 2.0479210810800135

&nbsp;     },

&nbsp;     "3SsnPorch\_present": {

&nbsp;       "mean": 0.01643835616438356,

&nbsp;       "std": 0.12719755605884858,

&nbsp;       "min": 0,

&nbsp;       "max": 1,

&nbsp;       "median": 0,

&nbsp;       "skewness": 7.613746375479383

&nbsp;     },

&nbsp;     "ScreenPorch\_present": {

&nbsp;       "mean": 0.07945205479452055,

&nbsp;       "std": 0.2705356827038955,

&nbsp;       "min": 0,

&nbsp;       "max": 1,

&nbsp;       "median": 0,

&nbsp;       "skewness": 3.113266422552932

&nbsp;     },

&nbsp;     "PoolArea\_present": {

&nbsp;       "mean": 0.004794520547945206,

&nbsp;       "std": 0.0690999532130089,

&nbsp;       "min": 0,

&nbsp;       "max": 1,

&nbsp;       "median": 0,

&nbsp;       "skewness": 14.352680446365197

&nbsp;     },

&nbsp;     "MiscVal\_present": {

&nbsp;       "mean": 0.03561643835616438,

&nbsp;       "std": 0.18539538765531705,

&nbsp;       "min": 0,

&nbsp;       "max": 1,

&nbsp;       "median": 0,

&nbsp;       "skewness": 5.016527994711962

&nbsp;     }

&nbsp;   },

&nbsp;   "categorical\_summary": {

&nbsp;     "MSZoning": {

&nbsp;       "unique\_count": 5,

&nbsp;       "top\_values": {

&nbsp;         "RL": 1151,

&nbsp;         "RM": 218,

&nbsp;         "FV": 65,

&nbsp;         "RH": 16,

&nbsp;         "C (all)": 10

&nbsp;       }

&nbsp;     },

&nbsp;     "Street": {

&nbsp;       "unique\_count": 2,

&nbsp;       "top\_values": {

&nbsp;         "Pave": 1454,

&nbsp;         "Grvl": 6

&nbsp;       }

&nbsp;     },

&nbsp;     "LotShape": {

&nbsp;       "unique\_count": 4,

&nbsp;       "top\_values": {

&nbsp;         "Reg": 925,

&nbsp;         "IR1": 484,

&nbsp;         "IR2": 41,

&nbsp;         "IR3": 10

&nbsp;       }

&nbsp;     },

&nbsp;     "LandContour": {

&nbsp;       "unique\_count": 4,

&nbsp;       "top\_values": {

&nbsp;         "Lvl": 1311,

&nbsp;         "Bnk": 63,

&nbsp;         "HLS": 50,

&nbsp;         "Low": 36

&nbsp;       }

&nbsp;     },

&nbsp;     "Utilities": {

&nbsp;       "unique\_count": 2,

&nbsp;       "top\_values": {

&nbsp;         "AllPub": 1459,

&nbsp;         "NoSeWa": 1

&nbsp;       }

&nbsp;     },

&nbsp;     "LotConfig": {

&nbsp;       "unique\_count": 5,

&nbsp;       "top\_values": {

&nbsp;         "Inside": 1052,

&nbsp;         "Corner": 263,

&nbsp;         "CulDSac": 94,

&nbsp;         "FR2": 47,

&nbsp;         "FR3": 4

&nbsp;       }

&nbsp;     },

&nbsp;     "LandSlope": {

&nbsp;       "unique\_count": 3,

&nbsp;       "top\_values": {

&nbsp;         "Gtl": 1382,

&nbsp;         "Mod": 65,

&nbsp;         "Sev": 13

&nbsp;       }

&nbsp;     },

&nbsp;     "Neighborhood": {

&nbsp;       "unique\_count": 25,

&nbsp;       "top\_values": {

&nbsp;         "NAmes": 225,

&nbsp;         "CollgCr": 150,

&nbsp;         "OldTown": 113,

&nbsp;         "Edwards": 100,

&nbsp;         "Somerst": 86

&nbsp;       }

&nbsp;     },

&nbsp;     "Condition1": {

&nbsp;       "unique\_count": 9,

&nbsp;       "top\_values": {

&nbsp;         "Norm": 1260,

&nbsp;         "Feedr": 81,

&nbsp;         "Artery": 48,

&nbsp;         "RRAn": 26,

&nbsp;         "PosN": 19

&nbsp;       }

&nbsp;     },

&nbsp;     "Condition2": {

&nbsp;       "unique\_count": 8,

&nbsp;       "top\_values": {

&nbsp;         "Norm": 1445,

&nbsp;         "Feedr": 6,

&nbsp;         "Artery": 2,

&nbsp;         "RRNn": 2,

&nbsp;         "PosN": 2

&nbsp;       }

&nbsp;     },

&nbsp;     "BldgType": {

&nbsp;       "unique\_count": 5,

&nbsp;       "top\_values": {

&nbsp;         "1Fam": 1220,

&nbsp;         "TwnhsE": 114,

&nbsp;         "Duplex": 52,

&nbsp;         "Twnhs": 43,

&nbsp;         "2fmCon": 31

&nbsp;       }

&nbsp;     },

&nbsp;     "HouseStyle": {

&nbsp;       "unique\_count": 8,

&nbsp;       "top\_values": {

&nbsp;         "1Story": 726,

&nbsp;         "2Story": 445,

&nbsp;         "1.5Fin": 154,

&nbsp;         "SLvl": 65,

&nbsp;         "SFoyer": 37

&nbsp;       }

&nbsp;     },

&nbsp;     "RoofStyle": {

&nbsp;       "unique\_count": 6,

&nbsp;       "top\_values": {

&nbsp;         "Gable": 1141,

&nbsp;         "Hip": 286,

&nbsp;         "Flat": 13,

&nbsp;         "Gambrel": 11,

&nbsp;         "Mansard": 7

&nbsp;       }

&nbsp;     },

&nbsp;     "RoofMatl": {

&nbsp;       "unique\_count": 8,

&nbsp;       "top\_values": {

&nbsp;         "CompShg": 1434,

&nbsp;         "Tar\&Grv": 11,

&nbsp;         "WdShngl": 6,

&nbsp;         "WdShake": 5,

&nbsp;         "Metal": 1

&nbsp;       }

&nbsp;     },

&nbsp;     "Exterior1st": {

&nbsp;       "unique\_count": 15,

&nbsp;       "top\_values": {

&nbsp;         "VinylSd": 515,

&nbsp;         "HdBoard": 222,

&nbsp;         "MetalSd": 220,

&nbsp;         "Wd Sdng": 206,

&nbsp;         "Plywood": 108

&nbsp;       }

&nbsp;     },

&nbsp;     "Exterior2nd": {

&nbsp;       "unique\_count": 16,

&nbsp;       "top\_values": {

&nbsp;         "VinylSd": 504,

&nbsp;         "MetalSd": 214,

&nbsp;         "HdBoard": 207,

&nbsp;         "Wd Sdng": 197,

&nbsp;         "Plywood": 142

&nbsp;       }

&nbsp;     },

&nbsp;     "ExterQual": {

&nbsp;       "unique\_count": 4,

&nbsp;       "top\_values": {

&nbsp;         "TA": 906,

&nbsp;         "Gd": 488,

&nbsp;         "Ex": 52,

&nbsp;         "Fa": 14

&nbsp;       }

&nbsp;     },

&nbsp;     "ExterCond": {

&nbsp;       "unique\_count": 5,

&nbsp;       "top\_values": {

&nbsp;         "TA": 1282,

&nbsp;         "Gd": 146,

&nbsp;         "Fa": 28,

&nbsp;         "Ex": 3,

&nbsp;         "Po": 1

&nbsp;       }

&nbsp;     },

&nbsp;     "Foundation": {

&nbsp;       "unique\_count": 6,

&nbsp;       "top\_values": {

&nbsp;         "PConc": 647,

&nbsp;         "CBlock": 634,

&nbsp;         "BrkTil": 146,

&nbsp;         "Slab": 24,

&nbsp;         "Stone": 6

&nbsp;       }

&nbsp;     },

&nbsp;     "BsmtQual": {

&nbsp;       "unique\_count": 5,

&nbsp;       "top\_values": {

&nbsp;         "TA": 649,

&nbsp;         "Gd": 618,

&nbsp;         "Ex": 121,

&nbsp;         "None": 37,

&nbsp;         "Fa": 35

&nbsp;       }

&nbsp;     },

&nbsp;     "BsmtCond": {

&nbsp;       "unique\_count": 5,

&nbsp;       "top\_values": {

&nbsp;         "TA": 1311,

&nbsp;         "Gd": 65,

&nbsp;         "Fa": 45,

&nbsp;         "None": 37,

&nbsp;         "Po": 2

&nbsp;       }

&nbsp;     },

&nbsp;     "BsmtExposure": {

&nbsp;       "unique\_count": 5,

&nbsp;       "top\_values": {

&nbsp;         "No": 953,

&nbsp;         "Av": 221,

&nbsp;         "Gd": 134,

&nbsp;         "Mn": 114,

&nbsp;         "None": 38

&nbsp;       }

&nbsp;     },

&nbsp;     "BsmtFinType1": {

&nbsp;       "unique\_count": 7,

&nbsp;       "top\_values": {

&nbsp;         "Unf": 430,

&nbsp;         "GLQ": 418,

&nbsp;         "ALQ": 220,

&nbsp;         "BLQ": 148,

&nbsp;         "Rec": 133

&nbsp;       }

&nbsp;     },

&nbsp;     "BsmtFinType2": {

&nbsp;       "unique\_count": 7,

&nbsp;       "top\_values": {

&nbsp;         "Unf": 1256,

&nbsp;         "Rec": 54,

&nbsp;         "LwQ": 46,

&nbsp;         "None": 38,

&nbsp;         "BLQ": 33

&nbsp;       }

&nbsp;     },

&nbsp;     "Heating": {

&nbsp;       "unique\_count": 6,

&nbsp;       "top\_values": {

&nbsp;         "GasA": 1428,

&nbsp;         "GasW": 18,

&nbsp;         "Grav": 7,

&nbsp;         "Wall": 4,

&nbsp;         "OthW": 2

&nbsp;       }

&nbsp;     },

&nbsp;     "HeatingQC": {

&nbsp;       "unique\_count": 5,

&nbsp;       "top\_values": {

&nbsp;         "Ex": 741,

&nbsp;         "TA": 428,

&nbsp;         "Gd": 241,

&nbsp;         "Fa": 49,

&nbsp;         "Po": 1

&nbsp;       }

&nbsp;     },

&nbsp;     "CentralAir": {

&nbsp;       "unique\_count": 2,

&nbsp;       "top\_values": {

&nbsp;         "Y": 1365,

&nbsp;         "N": 95

&nbsp;       }

&nbsp;     },

&nbsp;     "Electrical": {

&nbsp;       "unique\_count": 5,

&nbsp;       "top\_values": {

&nbsp;         "SBrkr": 1334,

&nbsp;         "FuseA": 94,

&nbsp;         "FuseF": 27,

&nbsp;         "FuseP": 3,

&nbsp;         "Mix": 1

&nbsp;       }

&nbsp;     },

&nbsp;     "KitchenQual": {

&nbsp;       "unique\_count": 4,

&nbsp;       "top\_values": {

&nbsp;         "TA": 735,

&nbsp;         "Gd": 586,

&nbsp;         "Ex": 100,

&nbsp;         "Fa": 39

&nbsp;       }

&nbsp;     },

&nbsp;     "Functional": {

&nbsp;       "unique\_count": 7,

&nbsp;       "top\_values": {

&nbsp;         "Typ": 1360,

&nbsp;         "Min2": 34,

&nbsp;         "Min1": 31,

&nbsp;         "Mod": 15,

&nbsp;         "Maj1": 14

&nbsp;       }

&nbsp;     },

&nbsp;     "FireplaceQu": {

&nbsp;       "unique\_count": 6,

&nbsp;       "top\_values": {

&nbsp;         "None": 690,

&nbsp;         "Gd": 380,

&nbsp;         "TA": 313,

&nbsp;         "Fa": 33,

&nbsp;         "Ex": 24

&nbsp;       }

&nbsp;     },

&nbsp;     "GarageType": {

&nbsp;       "unique\_count": 7,

&nbsp;       "top\_values": {

&nbsp;         "Attchd": 870,

&nbsp;         "Detchd": 387,

&nbsp;         "BuiltIn": 88,

&nbsp;         "None": 81,

&nbsp;         "Basment": 19

&nbsp;       }

&nbsp;     },

&nbsp;     "GarageFinish": {

&nbsp;       "unique\_count": 4,

&nbsp;       "top\_values": {

&nbsp;         "Unf": 605,

&nbsp;         "RFn": 422,

&nbsp;         "Fin": 352,

&nbsp;         "None": 81

&nbsp;       }

&nbsp;     },

&nbsp;     "GarageQual": {

&nbsp;       "unique\_count": 6,

&nbsp;       "top\_values": {

&nbsp;         "TA": 1311,

&nbsp;         "None": 81,

&nbsp;         "Fa": 48,

&nbsp;         "Gd": 14,

&nbsp;         "Ex": 3

&nbsp;       }

&nbsp;     },

&nbsp;     "GarageCond": {

&nbsp;       "unique\_count": 6,

&nbsp;       "top\_values": {

&nbsp;         "TA": 1326,

&nbsp;         "None": 81,

&nbsp;         "Fa": 35,

&nbsp;         "Gd": 9,

&nbsp;         "Po": 7

&nbsp;       }

&nbsp;     },

&nbsp;     "PavedDrive": {

&nbsp;       "unique\_count": 3,

&nbsp;       "top\_values": {

&nbsp;         "Y": 1340,

&nbsp;         "N": 90,

&nbsp;         "P": 30

&nbsp;       }

&nbsp;     },

&nbsp;     "SaleType": {

&nbsp;       "unique\_count": 9,

&nbsp;       "top\_values": {

&nbsp;         "WD": 1267,

&nbsp;         "New": 122,

&nbsp;         "COD": 43,

&nbsp;         "ConLD": 9,

&nbsp;         "ConLI": 5

&nbsp;       }

&nbsp;     },

&nbsp;     "SaleCondition": {

&nbsp;       "unique\_count": 6,

&nbsp;       "top\_values": {

&nbsp;         "Normal": 1198,

&nbsp;         "Partial": 125,

&nbsp;         "Abnorml": 101,

&nbsp;         "Family": 20,

&nbsp;         "Alloca": 12

&nbsp;       }

&nbsp;     }

&nbsp;   }

&nbsp; },

&nbsp; "data\_quality": {

&nbsp;   "missing\_report": {

&nbsp;     "high\_missing\_columns": \[],

&nbsp;     "moderate\_missing\_columns": \[]

&nbsp;   },

&nbsp;   "id\_like\_columns": \[],

&nbsp;   "high\_skew\_columns": \[

&nbsp;     "KitchenAbvGr"

&nbsp;   ],

&nbsp;   "low\_variance\_columns": \[],

&nbsp;   "high\_cardinality\_columns": \[],

&nbsp;   "candidate\_targets": \[

&nbsp;     "SalePrice",

&nbsp;     "GrLivArea",

&nbsp;     "BsmtUnfSF",

&nbsp;     "TotalBsmtSF",

&nbsp;     "1stFlrSF"

&nbsp;   ]

&nbsp; }

}



### /get\_full\_analysis : after cleaning response:-



{

&nbsp; "selected\_columns": {

&nbsp;   "numerical\_columns": \[

&nbsp;     "GrLivArea",

&nbsp;     "BsmtFinSF1",

&nbsp;     "BsmtUnfSF",

&nbsp;     "TotalBsmtSF"

&nbsp;   ],

&nbsp;   "categorical\_columns": \[

&nbsp;     "MSZoning",

&nbsp;     "LotShape",

&nbsp;     "LandContour",

&nbsp;     "LotConfig",

&nbsp;     "LandSlope"

&nbsp;   ],

&nbsp;   "target\_column": "SalePrice",

&nbsp;   "problem\_type": "regression",

&nbsp;   "correlation\_pairs": \[

&nbsp;     \[

&nbsp;       "BsmtFinSF1",

&nbsp;       "TotalBsmtSF"

&nbsp;     ],

&nbsp;     \[

&nbsp;       "BsmtFinSF1",

&nbsp;       "BsmtUnfSF"

&nbsp;     ],

&nbsp;     \[

&nbsp;       "GrLivArea",

&nbsp;       "TotalBsmtSF"

&nbsp;     ]

&nbsp;   ],

&nbsp;   "skewed\_columns": \[]

&nbsp; },

&nbsp;   "insights": {

&nbsp;   "general": {

&nbsp;     "summary": "The dataset has 1,460 rows and 75 columns (37 numerical, 38 categorical). 'SalePrice' is identified as the target variable for regression. 1 numerical feature(s) are highly skewed — log transformation is recommended.",

&nbsp;     "missing": \[],

&nbsp;     "skewness": \[],

&nbsp;     "correlation": \[],

&nbsp;     "target": "'SalePrice' is the regression target (selected from candidate targets)."

&nbsp;   },

&nbsp;   "key\_findings": \[

&nbsp;     "'GrLivArea' is very strongly correlated positively with 'SalePrice' (r = 0.71), indicating high predictive importance.",

&nbsp;     "'TotalBsmtSF' is strongly correlated positively with 'SalePrice' (r = 0.61), indicating high predictive importance.",

&nbsp;     "'BsmtFinSF1' is moderately correlated positively with 'SalePrice' (r = 0.39), indicating limited predictive importance."

&nbsp;   ],

&nbsp;   "feature\_importance": \[

&nbsp;     {

&nbsp;       "feature": "GrLivArea",

&nbsp;       "correlation": 0.709

&nbsp;     },

&nbsp;     {

&nbsp;       "feature": "TotalBsmtSF",

&nbsp;       "correlation": 0.614

&nbsp;     },

&nbsp;     {

&nbsp;       "feature": "BsmtFinSF1",

&nbsp;       "correlation": 0.386

&nbsp;     },

&nbsp;     {

&nbsp;       "feature": "BsmtUnfSF",

&nbsp;       "correlation": 0.214

&nbsp;     }

&nbsp;   ],

&nbsp;   "correlation": \[

&nbsp;     "'BsmtFinSF1' and 'TotalBsmtSF' have a strong positive correlation (r = 0.52) — multicollinearity risk if both are used as features.",

&nbsp;     "'BsmtFinSF1' and 'BsmtUnfSF' have a strong negative correlation (r = -0.50) — multicollinearity risk if both are used as features.",

&nbsp;     "'GrLivArea' and 'TotalBsmtSF' have a strong positive correlation (r = 0.45) — multicollinearity risk if both are used as features."

&nbsp;   ],

&nbsp;   "target\_analysis": \[

&nbsp;     "'GrLivArea' is positively related to 'SalePrice' (r = 0.71) — very strong signal.",

&nbsp;     "'TotalBsmtSF' is positively related to 'SalePrice' (r = 0.61) — strong signal.",

&nbsp;     "'BsmtFinSF1' is positively related to 'SalePrice' (r = 0.39) — moderate signal.",

&nbsp;     "'BsmtUnfSF' is positively related to 'SalePrice' (r = 0.21) — moderate signal.",

&nbsp;     "'SalePrice' varies across 'MSZoning': avg 214,014.1 for 'FV' vs 74,528.0 for 'C (all)' — this categorical split is predictive.",

&nbsp;     "'SalePrice' varies across 'LotShape': avg 239,833.4 for 'IR2' vs 164,754.8 for 'Reg' — this categorical split is predictive.",

&nbsp;     "'SalePrice' varies across 'LandContour': avg 231,533.9 for 'HLS' vs 143,104.1 for 'Bnk' — this categorical split is predictive."

&nbsp;   ],

&nbsp;   "risk\_flags": \[

&nbsp;     "Highly skewed features: 'KitchenAbvGr' — may distort distance-based and linear models."

&nbsp;   ],

&nbsp;   "recommendations": \[

&nbsp;     "Target variable 'SalePrice' identified for regression. Ensure it is not leaked into feature engineering steps."

&nbsp;   ],

&nbsp;   "llm": "\*\*1. Key Insights from the Selected Variables\*\*\\n\\n| Variable | What it tells us | Relationship to SalePrice |\\n|----------|-----------------|---------------------------|\\n| \*\*GrLivArea\*\* (above‑grade living area) | Largest positive driver of price – mean ≈ 1,515 sq ft, right‑skewed (skew ≈ 1.37). | Correlation with \*\*TotalBsmtSF\*\* (≈ 0.6) – houses that are large overall tend to command higher prices. |\\n| \*\*TotalBsmtSF\*\* (total basement area) | Strongly influences price – mean ≈ 1,057 sq ft, heavy right‑skew (skew ≈ 1.52). | Directly correlated with \*\*BsmtFinSF1\*\* (≈ 0.8) and also with \*\*GrLivArea\*\*. |\\n| \*\*BsmtFinSF1\*\* (finished basement sq ft) | Adds value beyond raw basement size – mean ≈ 444 sq ft, very right‑skewed (skew ≈ 1.69). | Highly correlated with \*\*TotalBsmtSF\*\* (≈ 0.8) and modestly with \*\*BsmtUnfSF\*\* (≈ 0.4). |\\n| \*\*BsmtUnfSF\*\* (unfinished basement sq ft) | Unfinished space has a weaker, sometimes negative, impact – mean ≈ 567 sq ft, moderate skew (≈ 0.92). | Correlates positively with \*\*TotalBsmtSF\*\* but less strongly than the finished portion. |\\n| \*\*Categorical features\*\* (MSZoning, LotShape, LandContour, LotConfig, LandSlope) | Capture location‑ and lot‑characteristics that affect desirability.  The dominant levels are: <br>‑ \*MSZoning\*: “RL” (Residential Low) 79 % of rows <br>‑ \*LotShape\*: “Reg” (regular) 63 % <br>‑ \*LandContour\*: “Lvl” (level) 90 % <br>‑ \*LotConfig\*: “Inside” 72 % <br>‑ \*LandSlope\*: “Gtl” (gentle) 95 % <br>These variables will mostly act as binary/one‑hot flags distinguishing a small subset of houses (e.g., irregular lots, cul‑de‑sacs) that command premium or discount prices. |\\n\\n\* \*\*Correlation pairs supplied\*\* confirm that the three basement‑related metrics move together, and that larger overall floor area (GrLivArea) tends to accompany a larger total basement.  Multicollinearity is therefore expected among these numeric predictors.\\n\\n\* \*\*SalePrice\*\* itself is heavily right‑skewed (skew ≈ 1.88, std ≈ 79 k).  A log‑transformation will make the target more Gaussian and improve linear‑model performance.\\n\\n---\\n\\n\*\*2. Data Issues to Address\*\*\\n\\n| Issue | Details | Remedy |\\n|-------|---------|--------|\\n| \*\*Missing values\*\* | Only 1 missing entry (0.07 %) in \*Electrical\*. | Impute with the mode (“SBrkr”) – impact negligible. |\\n| \*\*Skewed numeric predictors\*\* | All four selected numerics are right‑skewed (skew > 1). | Apply log‑(x + 1) or Box‑Cox transforms; consider Yeo‑Johnson for zero‑inclusive variables. |\\n| \*\*Multicollinearity\*\* | \*BsmtFinSF1\*, \*TotalBsmtSF\*, \*BsmtUnfSF\* are highly correlated. | – Either drop one (e.g., keep \*TotalBsmtSF\* and \*BsmtFinSF1\* only) or use dimensionality‑reduction (PCA) or regularisation (Ridge/Lasso) that tolerates collinearity. |\\n| \*\*Low‑variance categorical levels\*\* | Most categorical columns are dominated by a single level (e.g., “RL”, “Reg”). | Encode as one‑hot; rare levels can be grouped into “Other” to avoid sparse columns. |\\n| \*\*No explicit ID column\*\* | Dataset does not contain a unique identifier, but rows are already unique. | No action needed. |\\n| \*\*Potential outliers\*\* | Extreme values in basement and living‑area (e.g., \*BsmtFinSF1\* = 5,644 sq ft). | Detect via IQR or robust z‑scores; cap or Winsorise if they distort model training. |\\n\\n---\\n\\n\*\*3. Modelling Suggestions\*\*\\n\\n| Step | Recommendation | Why it helps |\\n|------|----------------|--------------|\\n| \*\*Target transformation\*\* | `y = log1p(SalePrice)` | Normalises distribution, stabilises variance, improves linear‑model fit. |\\n| \*\*Feature engineering\*\* | • `TotalLiving = GrLivArea + 1stFlrSF + 2ndFlrSF` (overall size)<br>• `BasementRatio = TotalBsmtSF / (GrLivArea + 1)` (relative basement size)<br>• Binary flags for rare lot shapes, cul‑de‑sacs, steep slopes | Captures interactions and non‑linear effects that raw variables miss. |\\n| \*\*Encoding\*\* | One‑hot encode the five selected categoricals (or use ordinal encoding if a natural order exists, e.g., \*LotShape\*). | Allows tree‑based and linear models to use the information. |\\n| \*\*Skewness handling\*\* | Log‑transform the four numeric predictors (add 1 to avoid log(0)). | Reduces right‑skew, aligns predictor distribution with linear assumptions. |\\n| \*\*Model families\*\* | • \*\*Linear models\*\* with Lasso/Ridge (regularisation mitigates multicollinearity).<br>• \*\*Tree‑based ensembles\*\* (Random Forest, Gradient Boosting, XGBoost) – naturally handle non‑linearity and interactions, no need for explicit scaling.<br>• \*\*Stacked/Blended\*\* approach – combine linear (for interpretability) and tree models (for predictive power). | Provides a balance of interpretability (coefficients) and performance (non‑linear capture). |\\n| \*\*Cross‑validation\*\* | Use 5‑fold CV stratified by \*SalePrice\* quantiles (or time‑based split if \*YrSold\* matters). | Gives robust error estimates and guards against over‑fitting to a particular train‑test split. |\\n| \*\*Evaluation metric\*\* | RMSE on the \*\*log‑price\*\* (or RMSLE after back‑transform). | Aligns with the transformed target and penalises large relative errors. |\\n| \*\*Feature selection\*\* | After encoding, run a variance‑inflation‑factor (VIF) check; drop variables with VIF > 10 or combine them via PCA if needed. | Keeps model parsimonious and reduces multicollinearity. |\\n\\n---\\n\\n\*\*4. Business Interpretation\*\*\\n\\n\* \*\*Living area is the primary price lever\*\* – every additional 100 sq ft of above‑grade living space translates into a noticeable increase in sale price. Marketing and design should therefore highlight spacious floor plans.\\n\\n\* \*\*Finished basement adds premium value\*\*, whereas unfinished basement contributes far less (and can even be a cost‑center). Renovation strategies that convert unfinished space to finished living area are likely to yield higher ROI.\\n\\n\* \*\*Lot characteristics matter, but only for a minority of homes\*\* – irregular shapes, steep slopes, or cul‑de‑sacs appear infrequently; when present they can either command a premium (e.g., “CulDSac” with privacy) or a discount (e.g., “IR3” irregular lot). Targeted pricing adjustments for these sub‑segments are advisable.\\n\\n\* \*\*Location zoning (MSZoning) dominates the categorical signal\*\* – the “RL” (low‑density residential) zone is the baseline; “FV” (floating village) and “RH” (high‑density residential) are less common and typically fetch higher prices. Developers can use zoning data to price new projects or to identify under‑priced parcels.\\n\\n\* \*\*Log‑price modelling aligns with market perception\*\* – buyers think in relative terms (percentage change) rather than absolute dollars. Presenting price forecasts on a log scale (or as % change) can improve communication with stakeholders.\\n\\n\* \*\*Actionable next steps for the business\*\*  \\n  1. \*\*Prioritise upgrades\*\* that increase \*GrLivArea\* or finish basement space.  \\n  2. \*\*Adjust listings\*\* for houses on irregular lots or steep slopes based on the learned premium/discount factors.  \\n  3. \*\*Use the model\*\* to flag properties that are priced below the predicted log‑price – these may represent acquisition opportunities or pricing errors.  \\n\\nIn short, the data confirms the classic real‑estate intuition: bigger, well‑finished homes in standard, level lots sell for more. By properly handling skewness, multicollinearity, and rare categorical levels, a robust regression (or blended) model can reliably quantify these effects and guide pricing, renovation, and acquisition decisions."

&nbsp; }

}


### /modeling: response:-


{

&nbsp; "session\_id": "1a76df98-425b-4436-83af-1f063519e769",

&nbsp; "problem\_type": "regression",

&nbsp; "target\_column": "SalePrice",

&nbsp; "metric\_name": "rmse",

&nbsp; "metric\_value": 26190.2865,

&nbsp; "extra\_metrics": {

&nbsp;   "r2\_score": 0.9106

&nbsp; },

&nbsp; "rows\_trained": 1168,

&nbsp; "rows\_tested": 292,

&nbsp; "n\_features": 243,

&nbsp; "feature\_importance": \[

&nbsp;   {

&nbsp;     "feature": "RoofMatl\_CompShg",

&nbsp;     "importance": 0.3323948752400259

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "RoofMatl\_Tar\&Grv",

&nbsp;     "importance": 0.227052589933149

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "GrLivArea",

&nbsp;     "importance": 0.20591034196951402

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "RoofMatl\_WdShngl",

&nbsp;     "importance": 0.15418169450275096

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "MSZoning\_RL",

&nbsp;     "importance": 0.13989532991503614

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "RoofMatl\_WdShake",

&nbsp;     "importance": 0.13297042062325526

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "MSZoning\_RM",

&nbsp;     "importance": 0.11705513391660322

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "GarageQual\_TA",

&nbsp;     "importance": 0.10409878605785876

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "MSZoning\_FV",

&nbsp;     "importance": 0.08042328642944475

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "RoofMatl\_Roll",

&nbsp;     "importance": 0.07911809218122862

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "GarageCond\_TA",

&nbsp;     "importance": 0.07857920129919624

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "2ndFlrSF",

&nbsp;     "importance": 0.07650513566189711

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "RoofMatl\_Metal",

&nbsp;     "importance": 0.07530023913919776

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "1stFlrSF",

&nbsp;     "importance": 0.0743795734010887

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "GarageQual\_Fa",

&nbsp;     "importance": 0.06662908652046748

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "TotalBsmtSF",

&nbsp;     "importance": 0.0637090157385967

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "YearBuilt",

&nbsp;     "importance": 0.06284372830022618

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "OverallQual",

&nbsp;     "importance": 0.05672182021507976

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "GarageType\_Attchd",

&nbsp;     "importance": 0.05496292967210203

&nbsp;   },

&nbsp;   {

&nbsp;     "feature": "GarageType\_Detchd",

&nbsp;     "importance": 0.04682390476140879

&nbsp;   }

&nbsp; ]

}



