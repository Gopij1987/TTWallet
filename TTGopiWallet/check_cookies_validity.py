from api_automation_TTGopiWallet import load_session

session = load_session()
if session:
    print("Session valid: cookies are working.")
else:
    print("Session invalid: cookies are expired or incorrect.")
