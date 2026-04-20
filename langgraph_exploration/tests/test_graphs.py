from lang_graph_exploration.graphs.conditional import run_sample as run_conditional
from lang_graph_exploration.graphs.hello_world import run_sample as run_hello_world
from lang_graph_exploration.graphs.looping import run_sample as run_looping
from lang_graph_exploration.graphs.multiple_inputs import run_sample as run_multiple_inputs
from lang_graph_exploration.graphs.sequential import run_sample as run_sequential


def test_hello_world_graph() -> None:
    result = run_hello_world()
    assert result["message"] == "Hey Bob, how is your day going?"


def test_multiple_inputs_graph() -> None:
    result = run_multiple_inputs()
    assert result["result"] == "Hi there Senthil, Your sum is 12"


def test_sequential_graph() -> None:
    result = run_sequential()
    assert result["final"] == "Hi Charlie! You are 20 years old!"


def test_conditional_graph() -> None:
    result = run_conditional()
    assert result["finalNumber"] == 5


def test_looping_graph() -> None:
    result = run_looping()
    assert result["name"] == "Hi there, Vaibhav"
    assert result["counter"] == 5
    assert len(result["number"]) == 5