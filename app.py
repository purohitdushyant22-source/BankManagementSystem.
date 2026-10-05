import json
import random
import string
from pathlib import Path

import streamlit as st


DATA_FILE = Path(__file__).with_name("data.json")


def load_accounts():
    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open(encoding="utf-8") as file:
            accounts = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        st.error(f"Could not read the accounts file: {error}")
        st.stop()

    if not isinstance(accounts, list):
        st.error("The accounts file has an invalid format. Expected a list of accounts.")
        st.stop()

    return accounts


def save_accounts(accounts):
    try:
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(accounts, file, indent=2)
    except OSError as error:
        st.error(f"Could not save the account changes: {error}")
        return False

    return True


def generate_account_number():
    characters = (
        random.choices(string.ascii_letters, k=3)
        + random.choices(string.digits, k=3)
        + random.choices("!@#$%^&*", k=1)
    )
    random.shuffle(characters)
    return "".join(characters)


def authenticate(accounts, account_number, pin):
    return next(
        (
            account
            for account in accounts
            if account.get("accountNo.") == account_number
            and str(account.get("pin")) == pin
        ),
        None,
    )


st.set_page_config(page_title="Bank Management System", page_icon="🏦")
st.title("🏦 Bank Management System")
st.caption("Create and manage your account, deposits, and withdrawals.")

accounts = load_accounts()
page = st.sidebar.radio(
    "Choose an action",
    (
        "Create account",
        "Deposit money",
        "Withdraw money",
        "Account details",
        "Update details",
        "Delete account",
    ),
)


if page == "Create account":
    st.header("Create a bank account")
    with st.form("create_account_form"):
        name = st.text_input("Full name")
        age = st.number_input("Age", min_value=0, max_value=120, step=1)
        email = st.text_input("Email address")
        pin = st.text_input("Choose a 4-digit PIN", type="password", max_chars=4)
        submitted = st.form_submit_button("Create account")

    if submitted:
        if not name.strip() or not email.strip():
            st.error("Please enter your name and email address.")
        elif age < 18:
            st.error("You must be at least 18 years old to create an account.")
        elif len(pin) != 4 or not pin.isdigit():
            st.error("Your PIN must contain exactly 4 digits.")
        else:
            account = {
                "name": name.strip(),
                "age": int(age),
                "email": email.strip(),
                "pin": pin,
                "accountNo.": generate_account_number(),
                "balance": 0,
            }
            accounts.append(account)
            if save_accounts(accounts):
                st.success("Account created successfully.")
                st.info(f"Your account number is: **{account['accountNo.']}**")
                st.warning("Keep your account number safe. It is needed to access your account.")


elif page in ("Deposit money", "Withdraw money", "Account details", "Update details", "Delete account"):
    st.header(page)
    with st.form("account_access_form"):
        account_number = st.text_input("Account number")
        pin = st.text_input("4-digit PIN", type="password", max_chars=4)

        if page in ("Deposit money", "Withdraw money"):
            amount = st.number_input(
                "Amount",
                min_value=1,
                max_value=10000 if page == "Deposit money" else 1000000000,
                step=1,
            )
        elif page == "Update details":
            new_name = st.text_input("New name (leave blank to keep current)")
            new_email = st.text_input("New email (leave blank to keep current)")
            new_pin = st.text_input(
                "New 4-digit PIN (leave blank to keep current)",
                type="password",
                max_chars=4,
            )
        elif page == "Delete account":
            confirm_deletion = st.checkbox("I understand this account deletion cannot be undone.")

        submitted = st.form_submit_button(page)

    if submitted:
        if len(pin) != 4 or not pin.isdigit():
            st.error("Enter a valid 4-digit PIN.")
        else:
            account = authenticate(accounts, account_number.strip(), pin)
            if account is None:
                st.error("No account was found with those credentials.")
            elif page == "Deposit money":
                account["balance"] += int(amount)
                if save_accounts(accounts):
                    st.success(f"Deposited {int(amount):,} successfully.")
                    st.metric("Updated balance", f"{account['balance']:,}")
            elif page == "Withdraw money":
                if account["balance"] < int(amount):
                    st.error("Insufficient funds.")
                else:
                    account["balance"] -= int(amount)
                    if save_accounts(accounts):
                        st.success(f"Withdrew {int(amount):,} successfully.")
                        st.metric("Updated balance", f"{account['balance']:,}")
            elif page == "Account details":
                st.success("Account verified.")
                st.subheader(f"Account details for {account['name']}")
                st.table(
                    [
                        {"Detail": "Name", "Information": account["name"]},
                        {"Detail": "Age", "Information": account["age"]},
                        {"Detail": "Email", "Information": account["email"]},
                        {
                            "Detail": "Account number",
                            "Information": account["accountNo."],
                        },
                        {"Detail": "Balance", "Information": f"{account['balance']:,}"},
                    ]
                )
            elif page == "Update details":
                if new_pin and (len(new_pin) != 4 or not new_pin.isdigit()):
                    st.error("The new PIN must contain exactly 4 digits.")
                elif new_name and not new_name.strip():
                    st.error("Name cannot contain only spaces.")
                elif new_email and not new_email.strip():
                    st.error("Email cannot contain only spaces.")
                else:
                    if new_name:
                        account["name"] = new_name.strip()
                    if new_email:
                        account["email"] = new_email.strip()
                    if new_pin:
                        account["pin"] = new_pin
                    if save_accounts(accounts):
                        st.success("Account details updated successfully.")
            elif page == "Delete account":
                if confirm_deletion:
                    accounts.remove(account)
                    if save_accounts(accounts):
                        st.success("Account deleted successfully.")
                else:
                    st.warning("Select the confirmation checkbox before deleting the account.")