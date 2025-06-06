"""Extract companies and leads from any web page.

This module scrapes a page with Playwright and then asks an LLM to return
structured company or lead data."""

from __future__ import annotations

import os
import logging
import argparse
import asyncio
from typing import List, Optional, Tuple, Type

from bs4 import BeautifulSoup
from pydantic import BaseModel
from openai import AsyncOpenAI

from utils import fetch_html_playwright, common

logger = logging.getLogger(__name__)


class Company(BaseModel):
    organization_name: str = ""
    organization_website: str = ""
    primary_domain_of_organization: str = ""
    link_to_more_information: str = ""
    organization_linkedin_url: str = ""


class CompanyList(BaseModel):
    companies: List[Company]


class Lead(BaseModel):
    first_name: str = ""
    last_name: str = ""
    user_linkedin_url: str = ""
    organization_name: str = ""
    organization_website: str = ""
    primary_domain_of_organization: str = ""
    link_to_more_information: str = ""
    organization_linkedin_url: str = ""
    email: str = ""
    phone: str = ""
    follower_count: int = 0


class LeadList(BaseModel):
    leads: List[Lead]


async def _get_structured_data_internal(prompt: str, model: Type[BaseModel]) -> Tuple[Optional[BaseModel], str]:
    """Send ``prompt`` to OpenAI and parse the response as ``model``."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        return None, "ERROR"

    client = AsyncOpenAI(api_key=api_key)
    try:
        response = await client.chat.completions.create(
            model=common.get_openai_model(),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content or ""
        if not text:
            return None, "ERROR"
        return model.parse_raw(text), "SUCCESS"
    except Exception:  # pragma: no cover - network failures etc.
        logger.exception("OpenAI call failed")
        return None, "ERROR"


async def _fetch_and_clean(url: str) -> str:
    html = await fetch_html_playwright.fetch_html(url)
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style", "meta", "code", "svg"]):
        tag.decompose()
    return str(soup)


async def extract_multiple_companies_from_webpage(url: str) -> List[Company]:
    html = await _fetch_and_clean(url)
    if not html:
        return []
    text = BeautifulSoup(html, "html.parser").get_text("\n", strip=True)
    prompt = (
        "Extract all companies mentioned in the text below.\n"
        f"Return JSON matching this schema:\n{CompanyList.schema_json(indent=2)}\n\n"
        f"Text:\n{text}"
    )
    result, status = await _get_structured_data_internal(prompt, CompanyList)
    if status != "SUCCESS" or result is None:
        return []
    return result.companies


async def extract_comapy_from_webpage(url: str) -> Optional[Company]:
    companies = await extract_multiple_companies_from_webpage(url)
    return companies[0] if companies else None


async def extract_multiple_leads_from_webpage(url: str) -> List[Lead]:
    html = await _fetch_and_clean(url)
    if not html:
        return []
    text = BeautifulSoup(html, "html.parser").get_text("\n", strip=True)
    prompt = (
        "Extract all leads mentioned in the text below.\n"
        f"Return JSON matching this schema:\n{LeadList.schema_json(indent=2)}\n\n"
        f"Text:\n{text}"
    )
    result, status = await _get_structured_data_internal(prompt, LeadList)
    if status != "SUCCESS" or result is None:
        return []
    return result.leads


async def extract_lead_from_webpage(url: str) -> Optional[Lead]:
    leads = await extract_multiple_leads_from_webpage(url)
    return leads[0] if leads else None


async def _run_cli(url: str, args: argparse.Namespace) -> None:
    if args.lead:
        result = await extract_lead_from_webpage(url)
        if result:
            print(result.json(indent=2))
        return
    if args.leads:
        result = await extract_multiple_leads_from_webpage(url)
        print("[]" if not result else LeadList(leads=result).json(indent=2))
        return
    if args.company:
        result = await extract_comapy_from_webpage(url)
        if result:
            print(result.json(indent=2))
        return
    if args.companies:
        result = await extract_multiple_companies_from_webpage(url)
        print("[]" if not result else CompanyList(companies=result).json(indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract leads or companies from a web page"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--lead", action="store_true", help="Fetch first lead")
    group.add_argument("--leads", action="store_true", help="Fetch all leads")
    group.add_argument("--company", action="store_true", help="Fetch first company")
    group.add_argument(
        "--companies", action="store_true", help="Fetch all companies"
    )
    parser.add_argument("url", help="Website URL")
    args = parser.parse_args()
    asyncio.run(_run_cli(args.url, args))


if __name__ == "__main__":
    main()

