-- stg_customers.sql
--
-- Staging model: cleans and standardizes the raw customer table before
-- any downstream analysis. This is the "semantic layer" step -- raw
-- source data is renamed, cast to sensible types, and given consistent
-- naming, so that any model or query built on top of this one doesn't
-- have to repeat that cleanup logic.

with source as (

    select * from {{ source('churn_data', 'customers') }}

),

renamed as (

    select
        customerID                                   as customer_id,
        gender,
        SeniorCitizen                                 as is_senior_citizen,
        Partner                                       as has_partner,
        Dependents                                    as has_dependents,
        tenure                                        as tenure_months,
        PhoneService                                  as has_phone_service,
        MultipleLines                                 as multiple_lines,
        InternetService                               as internet_service,
        OnlineSecurity                                as online_security,
        OnlineBackup                                  as online_backup,
        DeviceProtection                              as device_protection,
        TechSupport                                   as tech_support,
        StreamingTV                                   as streaming_tv,
        StreamingMovies                               as streaming_movies,
        Contract                                      as contract_type,
        PaperlessBilling                              as has_paperless_billing,
        PaymentMethod                                 as payment_method,
        MonthlyCharges                                as monthly_charges,
        safe_cast(TotalCharges as float64)             as total_charges,
        Churn                                         as has_churned

    from source

)

select * from renamed
