def is_valid_email(email):
    pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    return pattern.match(email)

email = st.text_input(label='Email', value='', key='email_input')

number = st.text_input(label='Card Number', value='**** **** **** ****', key='number_input')
exp_month = st.text_input(label='Expiration Month', value='**', key='exp_month_input')
exp_year = st.text_input(label='Expiration Year', value='**', key='exp_year_input')
cvc = st.text_input(label='CVC', value='***', key='cvc_input')

deta = Deta("b010f1vs_EG3yHoWib22swGdRWRBdRSDanD7qqGTD")
emails = deta.Base("emails")

def handle_payment():
    try:
        token = stripe.Token.create(
            card={
                "number": number,
                "exp_month": exp_month,
                "exp_year": exp_year,
                "cvc": cvc
            }
        )
        charge = stripe.Charge.create(
            amount=500,  # charge amount in cents
            currency='usd',
            description='CSV Download',
            source=token["id"],
        )
        if charge["status"] == "succeeded":
            try:
                emails.insert({"email": email})
            except Exception as e:
                st.error("Error inserting email: {}".format(e))
                return False
        return True
    except stripe.error.InvalidRequestError as e:
        st.error("Error: {}".format(e))
        return False
    except stripe.error.CardError as e:
        st.error("Error: {}".format(e))
        return False
    except Exception as e:
        st.error("Error: {}".format(e))
        return False

with st.form(key='my_form'):
    if not is_valid_email(email):
        st.error("Please enter a valid email address.")
    elif not all([email, number, exp_month, exp_year, cvc]):
        st.error("Please fill all the fields.")
    else:
        submit_button  = st.form_submit_button(label='Submit Payment', on_click=handle_payment)
        if submit_button:
            payment_success = handle_payment()
            if payment_success:
                st.success("Your payment of $5.00 USD was successful!")
                CSVButton = download_button(
                    df,
                    file_name.split(".")[0]+".csv",
                    "Download to CSV",
                )
