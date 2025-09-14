# linkedin_mcp_server/bridge/utils.py
"""
Utility functions for bridge/selenium compatibility.

Provides helper functions to determine session type and route scraping operations
to the appropriate implementation (bridge or direct WebDriver).
"""

import logging
from typing import Any, Dict, Union

from selenium import webdriver
from linkedin_scraper import Person, Company

from linkedin_mcp_server.bridge.session import BrowserSession
from linkedin_mcp_server.bridge.scraper import BridgePersonScraper, BridgeCompanyScraper, BridgeJobScraper

logger = logging.getLogger(__name__)


async def scrape_person_profile(linkedin_url: str, session_or_driver: Union[BrowserSession, webdriver.Chrome]) -> Dict[str, Any]:
    """
    Scrape person profile using either bridge session or direct WebDriver.
    
    Args:
        linkedin_url: LinkedIn profile URL
        session_or_driver: Either a BrowserSession (bridge) or Chrome WebDriver
        
    Returns:
        Dictionary containing profile data
    """
    try:
        if isinstance(session_or_driver, BrowserSession):
            # Use bridge scraper
            logger.info(f"Scraping profile via bridge: {linkedin_url}")
            scraper = BridgePersonScraper(linkedin_url, session_or_driver)
            profile_data = await scraper.scrape()
            
            # Convert to format compatible with existing code
            return {
                "name": profile_data.get("name", ""),
                "headline": profile_data.get("headline", ""),
                "location": profile_data.get("location", ""),
                "about": profile_data.get("about", ""),
                "experiences": [
                    {
                        "title": exp.get("title", ""),
                        "company": exp.get("company", ""),
                        "duration": exp.get("duration", ""),
                        "description": exp.get("description", ""),
                        "location": ""
                    }
                    for exp in profile_data.get("experience", [])
                ],
                "education": profile_data.get("education", []),
                "skills": profile_data.get("skills", []),
                "linkedin_url": linkedin_url,
                "extraction_method": "bridge"
            }
        else:
            # Use direct WebDriver with linkedin-scraper library
            logger.info(f"Scraping profile via WebDriver: {linkedin_url}")
            person = Person(linkedin_url, driver=session_or_driver, close_on_complete=False)
            
            # Convert to consistent format
            experiences = []
            if hasattr(person, 'experiences') and person.experiences:
                for exp in person.experiences:
                    experiences.append({
                        "title": getattr(exp, 'position_title', '') or '',
                        "company": getattr(exp, 'institution_name', '') or '',
                        "duration": getattr(exp, 'duration', '') or '',
                        "description": getattr(exp, 'description', '') or '',
                        "location": getattr(exp, 'location', '') or ''
                    })
            
            education = []
            if hasattr(person, 'educations') and person.educations:
                for edu in person.educations:
                    education.append({
                        "institution_name": getattr(edu, 'institution_name', '') or '',
                        "degree_name": getattr(edu, 'degree_name', '') or '',
                        "years": getattr(edu, 'years', '') or ''
                    })
            
            skills = []
            if hasattr(person, 'skills') and person.skills:
                skills = [str(skill) for skill in person.skills]
            
            return {
                "name": getattr(person, 'name', '') or '',
                "headline": getattr(person, 'headline', '') or '',
                "location": getattr(person, 'location', '') or '',
                "about": getattr(person, 'about', '') or '',
                "experiences": experiences,
                "education": education,
                "skills": skills,
                "linkedin_url": linkedin_url,
                "extraction_method": "webdriver"
            }
            
    except Exception as e:
        logger.error(f"Error scraping person profile {linkedin_url}: {e}")
        raise


async def scrape_company_profile(company_url: str, session_or_driver: Union[BrowserSession, webdriver.Chrome]) -> Dict[str, Any]:
    """
    Scrape company profile using either bridge session or direct WebDriver.
    
    Args:
        company_url: LinkedIn company URL
        session_or_driver: Either a BrowserSession (bridge) or Chrome WebDriver
        
    Returns:
        Dictionary containing company data
    """
    try:
        if isinstance(session_or_driver, BrowserSession):
            # Use bridge scraper
            logger.info(f"Scraping company via bridge: {company_url}")
            scraper = BridgeCompanyScraper(company_url, session_or_driver)
            company_data = await scraper.scrape()
            
            return {
                "name": company_data.get("name", ""),
                "tagline": company_data.get("tagline", ""),
                "industry": company_data.get("industry", ""),
                "company_size": company_data.get("company_size", ""),
                "headquarters": company_data.get("headquarters", ""),
                "founded": company_data.get("founded", ""),
                "about": company_data.get("about", ""),
                "website": company_data.get("website"),
                "employees": company_data.get("employees", []),
                "linkedin_url": company_url,
                "extraction_method": "bridge"
            }
        else:
            # Use direct WebDriver with linkedin-scraper library
            logger.info(f"Scraping company via WebDriver: {company_url}")
            company = Company(company_url, driver=session_or_driver, close_on_complete=False)
            
            return {
                "name": getattr(company, 'name', '') or '',
                "tagline": getattr(company, 'tagline', '') or '',
                "industry": getattr(company, 'industry', '') or '',
                "company_size": getattr(company, 'company_size', '') or '',
                "headquarters": getattr(company, 'headquarters', '') or '',
                "founded": getattr(company, 'founded', '') or '',
                "about": getattr(company, 'about', '') or '',
                "website": getattr(company, 'website', None),
                "employees": getattr(company, 'employees', []) or [],
                "linkedin_url": company_url,
                "extraction_method": "webdriver"
            }
            
    except Exception as e:
        logger.error(f"Error scraping company profile {company_url}: {e}")
        raise


async def scrape_job_details(job_url: str, session_or_driver: Union[BrowserSession, webdriver.Chrome]) -> Dict[str, Any]:
    """
    Scrape job details using either bridge session or direct WebDriver.
    
    Args:
        job_url: LinkedIn job URL
        session_or_driver: Either a BrowserSession (bridge) or Chrome WebDriver
        
    Returns:
        Dictionary containing job data
    """
    try:
        if isinstance(session_or_driver, BrowserSession):
            # Use bridge scraper
            logger.info(f"Scraping job via bridge: {job_url}")
            scraper = BridgeJobScraper(job_url, session_or_driver)
            job_data = await scraper.scrape()
            
            return {
                "title": job_data.get("title", ""),
                "company": job_data.get("company", ""),
                "location": job_data.get("location", ""),
                "description": job_data.get("description", ""),
                "seniority_level": job_data.get("seniority_level", ""),
                "employment_type": job_data.get("employment_type", ""),
                "industry": job_data.get("industry", ""),
                "job_functions": job_data.get("job_functions", []),
                "linkedin_url": job_url,
                "extraction_method": "bridge"
            }
        else:
            # Use direct WebDriver - for jobs we'll navigate and extract manually
            # since linkedin-scraper doesn't have a dedicated Job class
            logger.info(f"Scraping job via WebDriver: {job_url}")
            session_or_driver.get(job_url)
            
            # Basic job extraction using WebDriver
            try:
                title = session_or_driver.find_element("css selector", "h1").text.strip()
            except:
                title = "Could not extract title"
                
            try:
                company = session_or_driver.find_element("css selector", ".jobs-unified-top-card__company-name").text.strip()
            except:
                company = "Could not extract company"
                
            try:
                location = session_or_driver.find_element("css selector", ".jobs-unified-top-card__bullet").text.strip()
            except:
                location = "Could not extract location"
                
            try:
                description = session_or_driver.find_element("css selector", ".jobs-description__content").text.strip()
            except:
                description = "Could not extract description"
            
            return {
                "title": title,
                "company": company,
                "location": location,
                "description": description,
                "seniority_level": "",
                "employment_type": "",
                "industry": "",
                "job_functions": [],
                "linkedin_url": job_url,
                "extraction_method": "webdriver"
            }
            
    except Exception as e:
        logger.error(f"Error scraping job details {job_url}: {e}")
        raise


def is_bridge_session(session_or_driver: Union[BrowserSession, webdriver.Chrome]) -> bool:
    """
    Check if the provided object is a bridge session or WebDriver.
    
    Args:
        session_or_driver: Either a BrowserSession or Chrome WebDriver
        
    Returns:
        True if it's a bridge session, False if it's a WebDriver
    """
    return isinstance(session_or_driver, BrowserSession)