# %%
from real_intent.deliver.kvcore import KVCoreDeliverer
from real_intent.deliver.followupboss import AIFollowUpBossDeliverer

from dotenv import load_dotenv; load_dotenv()
import os

# %%
if (_logfire_token := os.getenv("LOGFIRE_WRITE_TOKEN")):
    import logfire
    logfire.configure(token=_logfire_token)

# %%
import pandas as pd

for i in range(1, 4 + 1):
    data = pd.read_csv(f"t{i}.csv")
    data.head()

    # %%
    def get_sentences(md5: str) -> list[str]:
        slice = data[data["md5"] == md5].iloc[0]

        POTENTIAL_SENTENCES = ["Residential", "Sellers", "Mortgages", "Brokers And Agents", "Pre-Movers", "First-Time Home Buyer", "RE Educational Content"]

        sentences = []
        for ps in POTENTIAL_SENTENCES:
            if ps in slice and slice[ps] == "x":
                sentences.append(ps)

        return sentences

    get_sentences(data["md5"].iloc[0])

    # %%
    per_lead_insights: dict[str, str] = {
        data.iloc[i]["md5"]: data.iloc[i]["insight"]
        for i in range(len(data))
    }

    # %%
    from real_intent import BigDBMClient
    from real_intent.schemas import UniqueMD5

    md5s = [UniqueMD5(md5=md5, sentences=get_sentences(md5)) for md5 in per_lead_insights.keys()]

    client = BigDBMClient(
        os.getenv("CLIENT_ID"),
        os.getenv("CLIENT_SECRET")
    )

    piis = client.pii_for_unique_md5s(md5s)
    len(piis)

    # %%
    deliverer = AIFollowUpBossDeliverer(
        api_key="",
        system=os.getenv("FOLLOWUPBOSS_SYSTEM"),
        system_key=os.getenv("FOLLOWUPBOSS_SYSTEM_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        tags=["realintent"],
        n_threads=6,
        per_lead_insights=per_lead_insights
    )

    # deliverer = KVCoreDeliverer(
    #     postmark_server_token="",
    #     from_email="",
    #     inboxing_address="",
    #     tag="realintent",
    #     per_lead_insights=per_lead_insights
    # )

    deliverer.deliver(piis)
