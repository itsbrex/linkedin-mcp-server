# linkedin_mcp_server/bridge/scraper.py
"""
Bridge-compatible LinkedIn scraper adapters.

Provides compatibility layer between the bridge browser sessions and the
linkedin-scraper library which expects direct WebDriver instances.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from linkedin_mcp_server.bridge.session import BrowserSession

logger = logging.getLogger(__name__)


class BridgePersonScraper:
    """Bridge-compatible person profile scraper."""

    def __init__(self, linkedin_url: str, session: BrowserSession):
        self.linkedin_url = linkedin_url
        self.session = session
        self.profile_data: Optional[Dict[str, Any]] = None

    async def scrape(self) -> Dict[str, Any]:
        """Scrape person profile using bridge session."""
        try:
            # Navigate to the LinkedIn profile
            await self.session.navigate(self.linkedin_url)
            
            # Wait for page to load
            await asyncio.sleep(3)

            # Extract profile data using JavaScript
            profile_script = """
            // Extract basic profile information
            const getTextContent = (selector) => {
                const element = document.querySelector(selector);
                return element ? element.textContent.trim() : null;
            };

            const getElementsText = (selector) => {
                const elements = document.querySelectorAll(selector);
                return Array.from(elements).map(el => el.textContent.trim()).filter(Boolean);
            };

            const profile = {
                name: getTextContent('h1'),
                headline: getTextContent('section[data-section="summary"] .text-body-medium'),
                location: getTextContent('.text-body-small.inline.t-black--light.break-words'),
                about: getTextContent('#about ~ .display-flex .text-body-medium'),
                experience: [],
                education: [],
                skills: []
            };

            // Extract experience
            const experienceElements = document.querySelectorAll('#experience ~ .pvs-list__container .display-flex');
            experienceElements.forEach(exp => {
                const title = exp.querySelector('.display-flex .t-bold')?.textContent?.trim();
                const company = exp.querySelector('.t-normal')?.textContent?.trim();
                const duration = exp.querySelector('.t-black--light')?.textContent?.trim();
                
                if (title && company) {
                    profile.experience.push({
                        title: title,
                        company: company,
                        duration: duration || '',
                        description: ''
                    });
                }
            });

            // Extract education
            const educationElements = document.querySelectorAll('#education ~ .pvs-list__container .display-flex');
            educationElements.forEach(edu => {
                const school = edu.querySelector('.t-bold')?.textContent?.trim();
                const degree = edu.querySelector('.t-normal')?.textContent?.trim();
                const years = edu.querySelector('.t-black--light')?.textContent?.trim();
                
                if (school) {
                    profile.education.push({
                        institution_name: school,
                        degree_name: degree || '',
                        years: years || ''
                    });
                }
            });

            // Extract skills
            const skillElements = document.querySelectorAll('#skills ~ .pvs-list__container .t-bold span[aria-hidden="true"]');
            skillElements.forEach(skill => {
                const skillName = skill.textContent?.trim();
                if (skillName) {
                    profile.skills.push(skillName);
                }
            });

            return profile;
            """

            # Execute the scraping script
            profile_data = await self.session.execute_script(profile_script)
            
            if not profile_data:
                # Fallback to basic extraction if script fails
                profile_data = await self._fallback_extraction()

            self.profile_data = profile_data
            return profile_data

        except Exception as e:
            logger.error(f"Error scraping profile {self.linkedin_url}: {e}")
            raise

    async def _fallback_extraction(self) -> Dict[str, Any]:
        """Fallback extraction method if JavaScript fails."""
        try:
            page_source = await self.session.get_page_source()
            current_url = await self.session.get_current_url()
            
            # Basic fallback data
            return {
                "name": "Profile extraction failed",
                "headline": "Could not extract profile data",
                "location": "",
                "about": "",
                "experience": [],
                "education": [],
                "skills": [],
                "url": current_url,
                "error": "JavaScript extraction failed, fallback used"
            }
        except Exception as e:
            logger.error(f"Fallback extraction also failed: {e}")
            return {
                "name": "Unknown",
                "headline": "Profile extraction failed completely",
                "location": "",
                "about": "",
                "experience": [],
                "education": [],
                "skills": [],
                "url": self.linkedin_url,
                "error": str(e)
            }


class BridgeCompanyScraper:
    """Bridge-compatible company profile scraper."""

    def __init__(self, company_url: str, session: BrowserSession):
        self.company_url = company_url
        self.session = session
        self.company_data: Optional[Dict[str, Any]] = None

    async def scrape(self) -> Dict[str, Any]:
        """Scrape company profile using bridge session."""
        try:
            # Navigate to the LinkedIn company page
            await self.session.navigate(self.company_url)
            
            # Wait for page to load
            await asyncio.sleep(3)

            # Extract company data using JavaScript
            company_script = """
            const getTextContent = (selector) => {
                const element = document.querySelector(selector);
                return element ? element.textContent.trim() : null;
            };

            const company = {
                name: getTextContent('h1'),
                tagline: getTextContent('.org-top-card-summary__tagline'),
                industry: getTextContent('.org-top-card-summary__industry'),
                company_size: getTextContent('.org-top-card-summary__info-item:nth-child(1) dd'),
                headquarters: getTextContent('.org-top-card-summary__info-item:nth-child(2) dd'),
                founded: getTextContent('.org-top-card-summary__info-item:nth-child(3) dd'),
                about: getTextContent('[data-section="about"] .text-body-medium'),
                website: null,
                employees: []
            };

            // Extract website from about section or contact info
            const aboutSection = document.querySelector('[data-section="about"]');
            if (aboutSection) {
                const links = aboutSection.querySelectorAll('a[href]');
                for (const link of links) {
                    const href = link.getAttribute('href');
                    if (href && !href.includes('linkedin.com')) {
                        company.website = href;
                        break;
                    }
                }
            }

            return company;
            """

            # Execute the scraping script
            company_data = await self.session.execute_script(company_script)
            
            if not company_data:
                # Fallback to basic extraction if script fails
                company_data = await self._fallback_extraction()

            self.company_data = company_data
            return company_data

        except Exception as e:
            logger.error(f"Error scraping company {self.company_url}: {e}")
            raise

    async def _fallback_extraction(self) -> Dict[str, Any]:
        """Fallback extraction method if JavaScript fails."""
        try:
            current_url = await self.session.get_current_url()
            
            # Basic fallback data
            return {
                "name": "Company extraction failed",
                "tagline": "Could not extract company data",
                "industry": "",
                "company_size": "",
                "headquarters": "",
                "founded": "",
                "about": "",
                "website": None,
                "employees": [],
                "url": current_url,
                "error": "JavaScript extraction failed, fallback used"
            }
        except Exception as e:
            logger.error(f"Fallback extraction also failed: {e}")
            return {
                "name": "Unknown",
                "tagline": "Company extraction failed completely",
                "industry": "",
                "company_size": "",
                "headquarters": "",
                "founded": "",
                "about": "",
                "website": None,
                "employees": [],
                "url": self.company_url,
                "error": str(e)
            }


class BridgeJobScraper:
    """Bridge-compatible job posting scraper."""

    def __init__(self, job_url: str, session: BrowserSession):
        self.job_url = job_url
        self.session = session
        self.job_data: Optional[Dict[str, Any]] = None

    async def scrape(self) -> Dict[str, Any]:
        """Scrape job posting using bridge session."""
        try:
            # Navigate to the LinkedIn job posting
            await self.session.navigate(self.job_url)
            
            # Wait for page to load
            await asyncio.sleep(3)

            # Extract job data using JavaScript
            job_script = """
            const getTextContent = (selector) => {
                const element = document.querySelector(selector);
                return element ? element.textContent.trim() : null;
            };

            const job = {
                title: getTextContent('h1'),
                company: getTextContent('.jobs-unified-top-card__company-name'),
                location: getTextContent('.jobs-unified-top-card__bullet'),
                description: getTextContent('.jobs-description__content'),
                seniority_level: '',
                employment_type: '',
                industry: '',
                job_functions: []
            };

            // Extract job criteria
            const criteriaElements = document.querySelectorAll('.jobs-description__content li');
            criteriaElements.forEach(criteria => {
                const text = criteria.textContent.trim();
                if (text.includes('Seniority level')) {
                    job.seniority_level = text.split(':')[1]?.trim() || '';
                } else if (text.includes('Employment type')) {
                    job.employment_type = text.split(':')[1]?.trim() || '';
                } else if (text.includes('Industry')) {
                    job.industry = text.split(':')[1]?.trim() || '';
                }
            });

            return job;
            """

            # Execute the scraping script
            job_data = await self.session.execute_script(job_script)
            
            if not job_data:
                # Fallback to basic extraction if script fails
                job_data = await self._fallback_extraction()

            self.job_data = job_data
            return job_data

        except Exception as e:
            logger.error(f"Error scraping job {self.job_url}: {e}")
            raise

    async def _fallback_extraction(self) -> Dict[str, Any]:
        """Fallback extraction method if JavaScript fails."""
        try:
            current_url = await self.session.get_current_url()
            
            # Basic fallback data
            return {
                "title": "Job extraction failed",
                "company": "Could not extract job data",
                "location": "",
                "description": "",
                "seniority_level": "",
                "employment_type": "",
                "industry": "",
                "job_functions": [],
                "url": current_url,
                "error": "JavaScript extraction failed, fallback used"
            }
        except Exception as e:
            logger.error(f"Fallback extraction also failed: {e}")
            return {
                "title": "Unknown",
                "company": "Job extraction failed completely",
                "location": "",
                "description": "",
                "seniority_level": "",
                "employment_type": "",
                "industry": "",
                "job_functions": [],
                "url": self.job_url,
                "error": str(e)
            }