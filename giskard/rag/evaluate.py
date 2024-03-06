from typing import Callable, Optional, Sequence, Union

import json
import logging

from ..llm.client import LLMClient, LLMMessage, get_default_client
from ..llm.errors import LLMGenerationError
from .knowledge_base import KnowledgeBase
from .metrics import Metric
from .report import RAGReport
from .testset import QATestset
from .testset_generation import generate_testset

logger = logging.getLogger(__name__)

CORRECTNESS_EVALUATION_PROMPT = """Your role is to test AI assistants. Your task consists in assessing whether a assistant output correctly answers a question. 
You are provided with the ground truth answer to the question. Your task is then to evaluate if the assistant answer is close to the ground thruth answer. 

You are auditing the following assistant:
{assistant_description}

Here is the question that was asked to the assistant, its output, and the expected ground truth answer delimited with XML tags:
<question>
{question}
</question>

<assistant_answer>
{assistant_answer}
</assistant_answer>

<ground_truth>
{ground_truth}
</ground_truth>

Think step by step and consider the assistant output in its entirety. Remember: you need to have a strong and sound reason to support your evaluation.
If the assistant answer is correct, return True. If the assistant answer is incorrect, return False along with the reason.
You must output a single JSON object with keys 'evaluation' and 'reason'. Make sure you return a valid JSON object."""


def evaluate(
    answers_fn: Union[Callable, Sequence[str]],
    knowledge_base: Optional[KnowledgeBase] = None,
    testset: Optional[QATestset] = None,
    llm_client: Optional[LLMClient] = None,
    assistant_description: str = "This assistant is a chatbot that answers question from users.",
    metrics: Optional[Sequence[Metric]] = None,
    conversation_support: bool = False,
    conversation_side: str = "client",
) -> RAGReport:
    """
    Evaluate an assistant by comparing its answers on a QATestset

    Parameters
    ----------
    answers_fn : Union[Callable, Sequence[str]]
        The prediction function of the assistant to evaluate or the list its answers on the testset.
    knowledge_base : KnowledgeBase, optional
        The knowledge base of the assistant to evaluate. If not provided, a testset must be provided.
    testset : QATestset, optional
        The test set to evaluate the assistant on. If not provided, a knowledge base must be provided and a default testset will be created from the knowledge base.
        Note that if the answers_fn is a list of answers, the testset is required.
    llm_client : LLMClient, optional
        The LLM client to use for the evaluation. If not provided, a default openai client will be used.
    assistant_description : str, optional
        Description of the assistant to be tested.
    metrics : Optional[Sequence[Metric]], optional
        The metrics to compute on the test set. If not provided, only the correctness of the answers will be computed.
    conversation_support : bool, optional
        Whether the assistant supports conversational questions or not. By default False.
    conversation_side : str, optional
        If conversation_support is True, specify how the conversation is handled by the assistant, either "client" or "server".
        When conversation is client sided, the assistant will receive the entire conversation history and the question at once.
        When conversation is server sided, the assistant will be sent each message of the conversation history one by one and finally the question.

    Returns
    -------
    RAGReport
        The report of the evaluation.
    """

    if testset is None and knowledge_base is None:
        raise ValueError("At least one of testset or knowledge base must be provided to the evaluate function.")

    if testset is None and not isinstance(answers_fn, Sequence):
        raise ValueError(
            "If the testset is not provided, the answers_fn must be a list of answers to ensure the matching between questions and answers."
        )

    if testset is None:
        testset = generate_testset(knowledge_base)

    answers = (
        answers_fn
        if isinstance(answers_fn, Sequence)
        else make_predictions(
            answers_fn, testset, conversation_support=conversation_support, conversation_side=conversation_side
        )
    )

    llm_client = llm_client or get_default_client()

    results = []
    for testset_item, answer in zip(testset.to_pandas().itertuples(), answers):
        try:
            out = llm_client.complete(
                messages=[
                    LLMMessage(
                        role="user",
                        content=CORRECTNESS_EVALUATION_PROMPT.format(
                            assistant_description=assistant_description,
                            question=testset_item.question,
                            assistant_answer=answer,
                            ground_truth=testset_item.reference_answer,
                        ),
                    ),
                ],
                temperature=0,
            )
            evaluation = json.loads(out.content, strict=False)
            evaluation["assistant_answer"] = answer
            results.append(evaluation)
        except Exception as err:
            print(out.content)
            raise LLMGenerationError(f"Error while evaluating the assistant: {err}")

    metrics_results = None
    if metrics is not None:
        metrics_results = {}
        for metric in metrics:
            metrics_results.update(metric(testset, answers, llm_client))

    return RAGReport(results, testset, knowledge_base, metrics_results)


def make_predictions(answers_fn, testset, conversation_support=False, conversation_side="client"):
    answers = []
    for sample in testset.to_pandas().itertuples():
        if conversation_support and len(sample.conversation_history) > 0:
            conversation = []
            for message in sample.conversation_history + [dict(role="client", content=sample.question)]:
                conversation.append(message)
                if conversation_side == "client":
                    assistant_answer = answers_fn(conversation)
                elif conversation_side == "server":
                    assistant_answer = answers_fn(message["content"])

                conversation.append(dict(role="assistant", content=assistant_answer))
            answers.append(conversation[-1]["content"])
        else:
            answers.append(answers_fn(sample.question))

    return answers
