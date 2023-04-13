import rigatoni
import asyncio


def print_method():
    print("Method on server called!")


starting_components = [
    rigatoni.StartingComponent(rigatoni.Method, {"name": "print", "arg_doc": []}, print_method)
]

asyncio.run(rigatoni.start_server(50000, starting_state=starting_components))