"""
hypothesis_test.py

A hypothesis-driven statistical analysis of the Telco Customer Churn
dataset. Rather than only reporting descriptive statistics (churn rate
per category), this script formally tests whether the observed
differences in churn rate across categories are statistically
significant, using a chi-squared test of independence.

I built this to complement ask_the_data.py: that script answers
"what happened" (descriptive, AI-assisted), while this script answers
"is this difference real, or could it be due to chance" (inferential).

Requires: pandas, scipy
    pip install pandas scipy --break-system-packages

Data: IBM Telco Customer Churn dataset (public, via Kaggle)
https://www.kaggle.com/datasets/blastchar/telco-customer-churn
"""

import pandas as pd
from scipy.stats import chi2_contingency

CSV_PATH = "WA_Fn-UseC_-Telco-Customer-Churn.csv"
ALPHA = 0.05  # significance threshold


def run_chi_squared_test(df: pd.DataFrame, category_column: str, hypothesis: str):
    """
    Run a chi-squared test of independence between a categorical column
    and Churn, and print a plain-language interpretation of the result.
    """
    print(f"\n{'=' * 70}")
    print(f"Hypothesis: {hypothesis}")
    print(f"{'=' * 70}")

    contingency_table = pd.crosstab(df[category_column], df["Churn"])
    print("\nObserved counts:")
    print(contingency_table)

    chi2, p_value, dof, expected = chi2_contingency(contingency_table)

    print(f"\nChi-squared statistic: {chi2:.2f}")
    print(f"Degrees of freedom: {dof}")
    print(f"p-value: {p_value:.2e}")

    if p_value < ALPHA:
        print(
            f"\nResult: p < {ALPHA} -> REJECT the null hypothesis. "
            f"There is a statistically significant relationship between "
            f"{category_column} and Churn."
        )
    else:
        print(
            f"\nResult: p >= {ALPHA} -> FAIL TO REJECT the null hypothesis. "
            f"No statistically significant relationship found between "
            f"{category_column} and Churn."
        )

    # Show the churn rate per category alongside the test result, so the
    # statistical significance can be read together with the practical
    # size of the effect (a significant result can still be a small effect).
    churn_rate = df.groupby(category_column)["Churn"].apply(
        lambda x: (x == "Yes").mean() * 100
    ).round(1)
    print(f"\nChurn rate by {category_column}:")
    print(churn_rate)


def main():
    df = pd.read_csv(CSV_PATH)

    # Null hypothesis for each test: churn is independent of the category
    # (i.e. the category has no relationship with whether a customer leaves).

    run_chi_squared_test(
        df,
        "Contract",
        "Churn is independent of contract type "
        "(month-to-month vs one-year vs two-year).",
    )

    run_chi_squared_test(
        df,
        "InternetService",
        "Churn is independent of internet service type "
        "(DSL vs Fiber optic vs No internet).",
    )

    run_chi_squared_test(
        df,
        "PaymentMethod",
        "Churn is independent of payment method.",
    )


if __name__ == "__main__":
    main()
