from letitbe_router.agents import DEFAULT_AGENTS, CliAgent
from letitbe_router.executor import Executor, build_command


def test_build_command_substitutes_prompt_without_shell():
    command = build_command(["python", "-c", "print('{prompt}')"], "hello; rm -rf /")

    assert command == ["python", "-c", "print('hello; rm -rf /')"]


def test_build_command_treats_unknown_braces_as_literal_text():
    command = build_command(("runner", "literal {not_prompt}", "{prompt}"), "hello")

    assert command == ["runner", "literal {not_prompt}", "hello"]


def test_executor_runs_selected_agent_command():
    agent = CliAgent(
        name="test-echo",
        command=("python", "-c", "import sys; print(sys.argv[1])", "{prompt}"),
        description="test echo",
    )
    result = Executor(timeout_seconds=5).run(agent, "hello")

    assert result.returncode == 0
    assert result.agent == "test-echo"
    assert "hello" in result.stdout


def test_default_agent_command_shapes_are_non_interactive():
    assert DEFAULT_AGENTS["codex-cli"].command[:2] == ("codex", "exec")
    assert "{prompt}" in DEFAULT_AGENTS["codex-cli"].command
    assert DEFAULT_AGENTS["gemini-cli"].command[:2] == ("gemini", "--prompt")
    assert DEFAULT_AGENTS["claude-code"].command[:2] == ("claude", "--print")


def test_executor_does_not_inherit_stdin():
    agent = CliAgent(
        name="stdin-check",
        command=(
            "python",
            "-c",
            "import sys; data=sys.stdin.read(); print('EMPTY' if data == '' else data)",
        ),
        description="stdin check",
    )

    result = Executor(timeout_seconds=5).run(agent, "ignored")

    assert result.returncode == 0
    assert result.stdout.strip() == "EMPTY"
