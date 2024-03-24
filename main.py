from dotenv import load_dotenv

# from app.scripts.azure.cost import run_azure_cost
from app.scripts.aws.main_cost import run_aws_cost_main
# from app.scripts.aws.test_cost import run_aws_cost_test

# Call the function from aws_cost_main.py
# run_azure_cost()
run_aws_cost_main()
# run_aws_cost_test()
