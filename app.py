import streamlit as st
import stripe
import pandas as pd
from glom import glom
import requests
import json
from pandas import json_normalize 
import io
from deta import Deta
import re

###################################
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import JsCode

###################################

from functionforDownloadButtons import download_button

###################################

stripe.api_key = 'sk_test_51MJj4EEKVq034p44ta07zOSkllukZWT9MSYZP7e3js62Lxc06gAhLpc4fZ1m4sHMSEsgZmOa2WjWifUK32m5RQBM00PxzHrDR0'

def _max_width_():
    max_width_str = f"max-width: 1800px;"
    st.markdown(
        f"""
    <style>
    .reportview-container .main .block-container{{
        {max_width_str}
    }}
    </style>    
    """,
        unsafe_allow_html=True,
    )

st.set_page_config(page_icon="https://i.imgur.com/y2i91bJ.png", page_title="Remodule")
st.image(
    "https://i.imgur.com/P7PyXuk.png",
    width=100,
)
st.title("JSON to CSV Converter by Remodule")

c29, c30, c31 = st.columns([1, 6, 1])

with c30:

    uploaded_file = st.file_uploader(
        "",
        key="1",
        help="To activate 'wide mode', go to the hamburger menu > Settings > turn on 'wide mode'",
    )

    # uploaded_file = st.text_input('Or copy and paste file here 👇')
    # uploaded_file = st.write(uploaded_file)

    if uploaded_file is not None:
        file_container = st.expander("Check your uploaded .json or .txt file")
        file_contents = uploaded_file.read()
        file_name = uploaded_file.name
        file_contents_str = file_contents.decode("utf-8")
        
        if isinstance(file_contents_str, bytes):
        # data is in bytes format, so it needs to be decoded
            json_data = json.loads(file_contents_str.decode())
        else:
        # data is already in a string format, so it does not need to be decoded
            json_data = json.loads(file_contents_str)
        if isinstance(json_data, dict):
        # data is in bytes format, so it needs to be decoded
            df = pd.json_normalize(json_data)
        else:
        # data is already in a string format, so it does not need to be decoded
            df = pd.read_json(file_contents_str)
            
        df_list = []
        df_exp = []
        cols = []
        columns_to_expand = []
        counts = {}

        def flatten(data):
            flat_data = {}
            # Handling case where data is a list
            if isinstance(data, list):
                for element in data:
                    if isinstance(element, dict):
                        nested_data = flatten(element)
                        for nested_key, nested_value in nested_data.items():
                            flat_key = f"{nested_key}"
                            flat_data[flat_key] = nested_value
                    else:
                        flat_data[key] = element
            # Handling case where data is a dictionary
            elif isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        nested_data = flatten(value)
                        for nested_key, nested_value in nested_data.items():
                            flat_key = f"{key}.{nested_key}"
                            flat_data[flat_key] = nested_value
                    elif isinstance(value, list):
                        flat_data[key] = value
                    else:
                        flat_data[key] = value
            return flat_data

        def get_columns_to_expand(df):
            for column in df.columns:
                if isinstance(df[column].iloc[0], (list, tuple)):
                    columns_to_expand.append(column)
            return columns_to_expand

        def expand_columns(df):
            columns_to_expand = get_columns_to_expand(df)
            for column in columns_to_expand:
                df_temp = df[column].apply(pd.Series)
                if not df_temp.empty:
                    df_temp.columns = ['{}.{}'.format(column, i) for i in range(len(df_temp.columns))]
                    df_exp.append(df_temp)
            if df_exp:
                df_expanded = pd.concat(df_exp, axis=1)
                return df_expanded
            else:
                return df

        def get_json_columns_to_expand(df):
            json_cols = [col for col in df.columns if df[col].apply(lambda x: type(x) == list and len(x)>0 and all(isinstance(i, dict) for i in x)).any()]
            return json_cols[0] if json_cols else ''

        def get_json_columns_to_drop(df):
            json_cols = [col for col in df.columns if df[col].apply(lambda x: type(x) == list and len(x)>0 and all(isinstance(i, dict) for i in x)).any()]
            return json_cols

        # Flatten the JSON data
        flattened_data = flatten(json_data)

        if isinstance(json_data, list):
            # Normalize the data in the list
            df = pd.json_normalize(json_data)
            df_list.append(df)

        elif isinstance(flattened_data, dict):
            for root_name, value in flattened_data.items():
                if isinstance(value, list) and all(isinstance(i, list) for i in value):
                    df = pd.DataFrame(value)
                    df.columns = [f'{root_name}.{i}' for i in range(len(df.columns))]  # rename the columns
                    df_list.append(df)
                elif isinstance(value, list) and all(isinstance(i, dict) for i in value):
                    df = pd.json_normalize(value, errors='ignore')
                    df_list.append(df)
                elif not isinstance(value, list):
                    df = pd.DataFrame({root_name: value}, index=[0])
                    df_list.append(df)
                else:
                    df = pd.DataFrame({root_name: dict}, index=[0])
                    df_list.append(df)

        # Concatenate the dataframes into a single dataframe
        df = pd.concat(df_list, axis=1, join='outer')

        for column in df.columns:
            if column in counts:
                counts[column] += 1
                cols.append(f'{column}_{counts[column]}')
            else:
                counts[column] = 1
                cols.append(column)
                
        df.columns = cols
        df = pd.json_normalize(json.loads(df.to_json(orient="records")), errors='ignore')
        df_expanded = expand_columns(df)
        get_col = get_columns_to_expand(df)
        df_drop = df.drop(get_col, axis=1, inplace=True)
        df_merged = pd.concat([df, df_expanded], axis=1, join='inner')
        df = df_merged
        df = df.loc[:,~df.columns.duplicated()].copy()
        col_json = get_json_columns_to_expand(df)
        drop_json = get_json_columns_to_drop(df)
        if col_json == '':
            pass
        else:
            df1 = (df[col_json].apply(pd.Series).merge(df, left_index=True, right_index = True))
            df_json = pd.json_normalize(json.loads(df1.to_json(orient="records")), errors='ignore')
            df_json.drop(columns=drop_json, inplace=True)
            df_json.dropna(how='all', axis=1, inplace=True)
            df = df_json

        # Display the resulting dataframe
        
        uploaded_file.seek(0)
        file_container.write(df)

    else:
        st.info(
            f"""
                👆 Upload a .json or .txt file first. Sample to try: [fees.json](https://api.llama.fi/overview/fees?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true&dataType=dailyFees)
                """
        )

        st.stop()

from st_aggrid import GridUpdateMode, DataReturnMode

gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
gb.configure_column(df.columns[0], headerCheckboxSelection=True)
gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=10)
gb.configure_selection(selection_mode="multiple", use_checkbox=True)
gb.configure_side_bar()  # side_bar is clearly a typo :) should by sidebar
gridOptions = gb.build()

st.success(
    f"""
        💡 Tip! Hold the shift key when selecting rows to select multiple rows at once!
        """
)

response = AgGrid(
    df,
    gridOptions=gridOptions,
    enable_enterprise_modules=False,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    fit_columns_on_grid_load=False,
    allow_unsafe_jscode=True,
)

df = pd.DataFrame(response["selected_rows"])
if '_selectedRowNodeInfo' in df.columns:
    df = df.drop(['_selectedRowNodeInfo'], axis=1)
df = df

st.subheader("Snapshot of filtered data will appear below 👇 ")
st.text("")

st.table(df.head(5))

st.text("")

c29, c30, c31 = st.columns([1, 1, 2])

with c29:

    CSVButton = download_button(
        df,
        "File.csv",
        "Download to CSV",
    )

st.markdown("""
<a href="https://www.buymeacoffee.com/remodule">
  <img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" width="140" height="40"/>
</a>
""", unsafe_allow_html=True)

# def is_valid_email(email):
#     return re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'+"", email)

# email = st.text_input(label='Email', value='', key='email_input')

# if email.strip() == "":
#     st.error("Email field cannot be empty.")
# elif not is_valid_email(email):
#     st.error("Invalid email address.")

# number = st.text_input(label='Card Number', value='**** **** **** ****', key='number_input')
# exp_month = st.text_input(label='Expiration Month', value='**', key='exp_month_input')
# exp_year = st.text_input(label='Expiration Year', value='**', key='exp_year_input')
# cvc = st.text_input(label='CVC', value='***', key='cvc_input')

# deta = Deta("b010f1vs_EG3yHoWib22swGdRWRBdRSDanD7qqGTD")
# emails = deta.Base("emails")

# def handle_payment():
#     if not all([email, number, exp_month, exp_year, cvc]):
#         return False
#     try:
#         token = stripe.Token.create(
#             card={
#                 "number": number,
#                 "exp_month": exp_month,
#                 "exp_year": exp_year,
#                 "cvc": cvc
#             }
#         )
#     except stripe.error.InvalidRequestError as e:
#         st.error("Error: {}".format(e))
#         return False
#     except Exception as e:
#         st.error("Error: {}".format(e))
#         return False
#     try:
#         charge = stripe.Charge.create(
#             amount=500,  # charge amount in cents
#             currency='usd',
#             description='CSV Download',
#             source=token["id"],
#         )
#         if charge["status"] == "succeeded":
#             try:
#                 emails.insert({"email": email})
#             except Exception as e:
#                 st.error("Error inserting email: {}".format(e))
#                 return False
#         return True
#     except stripe.error.CardError as e:
#         st.error("Error: {}".format(e))
#         return False
        
# with st.form(key='my_form'):
#     submit_button  = st.form_submit_button(label='Submit Payment', on_click=handle_payment)
#     if submit_button:
#         payment_success = handle_payment()
#         if payment_success:
#             st.success("Your payment of $5.00 USD was successful!")
#             CSVButton = download_button(
#                 df,
#                 file_name.split(".")[0]+".csv",
#                 "Download to CSV",
#                 )
