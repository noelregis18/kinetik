import os
from github import Github
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from textblob import TextBlob
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import re
import requests
from urllib.parse import urlparse

# Initialize Rich console for beautiful output
console = Console()

def get_github_client():
    """Initialize and return a GitHub client with authentication."""
    token = "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"
    return Github(token)

def find_live_website(repo):
    """Find live website URL from repository description and README."""
    website_url = None
    
    # Check repository description
    if repo.description:
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', repo.description)
        if urls:
            website_url = urls[0]
    
    # Check README
    try:
        readme = repo.get_readme()
        readme_content = readme.decoded_content.decode()
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', readme_content)
        if urls:
            website_url = urls[0]
    except:
        pass
    
    # Verify if website is live
    if website_url:
        try:
            response = requests.head(website_url, timeout=5)
            if response.status_code == 200:
                return website_url
        except:
            pass
    
    return None

def get_contributor_stats(repo):
    """Get detailed contributor statistics."""
    contributors = []
    try:
        for contributor in repo.get_contributors():
            commits = repo.get_commits(author=contributor.login)
            contributors.append({
                'name': contributor.login,
                'commits': commits.totalCount,
                'avatar_url': contributor.avatar_url
            })
    except:
        pass
    return sorted(contributors, key=lambda x: x['commits'], reverse=True)

def calculate_health_score(repo):
    """Calculate repository health score based on various metrics."""
    score = 0
    max_score = 100
    
    # Check README (20 points)
    try:
        readme = repo.get_readme()
        if readme:
            score += 20
    except:
        pass
    
    # Check documentation (10 points)
    if repo.has_wiki:
        score += 10
    
    # Check issues and pull requests (15 points)
    open_issues = repo.open_issues_count
    if open_issues < 10:
        score += 15
    elif open_issues < 20:
        score += 10
    elif open_issues < 30:
        score += 5
    
    # Check recent activity (20 points)
    commits = list(repo.get_commits(since=datetime.now() - timedelta(days=30)))
    if len(commits) > 20:
        score += 20
    elif len(commits) > 10:
        score += 15
    elif len(commits) > 5:
        score += 10
    
    # Check stars and forks (15 points)
    if repo.stargazers_count > 100:
        score += 8
    elif repo.stargazers_count > 50:
        score += 5
    elif repo.stargazers_count > 10:
        score += 3
    
    if repo.forks_count > 50:
        score += 7
    elif repo.forks_count > 20:
        score += 5
    elif repo.forks_count > 5:
        score += 3
    
    # Check license (10 points)
    if repo.license:
        score += 10
    
    # Check live website (10 points)
    if find_live_website(repo):
        score += 10
    
    return min(score, max_score)

def get_technology_stack(repo):
    """Get detailed technology stack information."""
    languages = repo.get_languages()
    total_bytes = sum(languages.values())
    
    tech_stack = []
    for lang, bytes in languages.items():
        percentage = (bytes / total_bytes) * 100
        tech_stack.append({
            'language': lang,
            'percentage': percentage,
            'bytes': bytes
        })
    
    return sorted(tech_stack, key=lambda x: x['percentage'], reverse=True)

def analyze_sentiment(text):
    """Analyze sentiment of text using TextBlob."""
    if not text:
        return 0
    return TextBlob(text).sentiment.polarity

def analyze_repository(repo_url):
    """Analyze a GitHub repository and return insights."""
    try:
        # Initialize GitHub client
        g = get_github_client()
        if not g:
            return None

        # Extract owner and repo name from URL
        parts = repo_url.strip('/').split('/')
        if len(parts) < 2:
            console.print("[bold red]Error:[/bold red] Invalid repository URL. Please provide a valid GitHub repository URL.")
            return None
        
        owner, repo_name = parts[-2], parts[-1]
        
        # Get repository
        repo = g.get_repo(f"{owner}/{repo_name}")
        
        # Calculate health score
        health_score = calculate_health_score(repo)
        
        # Analyze README sentiment
        readme_sentiment = 0
        try:
            readme = repo.get_readme()
            readme_content = readme.decoded_content.decode()
            readme_sentiment = analyze_sentiment(readme_content)
        except:
            pass
        
        # Get live website
        live_website = find_live_website(repo)
        
        # Get contributor stats
        contributors = get_contributor_stats(repo)
        
        # Get technology stack
        tech_stack = get_technology_stack(repo)
        
        # Collect repository data
        repo_data = {
            'name': repo.name,
            'description': repo.description,
            'stars': repo.stargazers_count,
            'forks': repo.forks_count,
            'open_issues': repo.open_issues_count,
            'language': repo.language,
            'created_at': repo.created_at,
            'last_updated': repo.updated_at,
            'size': repo.size,
            'topics': repo.get_topics(),
            'contributors': contributors,
            'commits': repo.get_commits().totalCount,
            'branches': repo.get_branches().totalCount,
            'releases': repo.get_releases().totalCount,
            'license': repo.license.name if repo.license else None,
            'license_url': repo.license.url if repo.license else None,
            'languages': repo.get_languages(),
            'health_score': health_score,
            'readme_sentiment': readme_sentiment,
            'live_website': live_website,
            'tech_stack': tech_stack
        }
        
        # Display results
        display_results(repo_data)
        
        return repo_data
        
    except Exception as e:
        console.print(f"[bold red]Error analyzing repository:[/bold red] {str(e)}")
        return None

def display_results(repo_data):
    """Display the analysis results in a formatted table."""
    # Create main table
    table = Table(title=f"\nRepository Analysis: {repo_data['name']}")
    
    # Add columns
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    # Add rows
    table.add_row("Description", repo_data['description'] or "No description")
    table.add_row("Stars", str(repo_data['stars']))
    table.add_row("Forks", str(repo_data['forks']))
    table.add_row("Open Issues", str(repo_data['open_issues']))
    table.add_row("Primary Language", repo_data['language'] or "Not specified")
    table.add_row("Created At", str(repo_data['created_at']))
    table.add_row("Last Updated", str(repo_data['last_updated']))
    table.add_row("Size", f"{repo_data['size']} KB")
    table.add_row("Topics", ", ".join(repo_data['topics']) or "No topics")
    table.add_row("Total Commits", str(repo_data['commits']))
    table.add_row("Branches", str(repo_data['branches']))
    table.add_row("Releases", str(repo_data['releases']))
    table.add_row("License", repo_data['license'] or "No license")
    if repo_data['license_url']:
        table.add_row("License URL", repo_data['license_url'])
    table.add_row("Health Score", f"{repo_data['health_score']}/100")
    table.add_row("README Sentiment", f"{repo_data['readme_sentiment']:.2f}")
    if repo_data['live_website']:
        table.add_row("Live Website", repo_data['live_website'])
    
    # Display table
    console.print(table)
    
    # Display technology stack
    if repo_data['tech_stack']:
        tech_table = Table(title="\nTechnology Stack")
        tech_table.add_column("Language", style="cyan")
        tech_table.add_column("Percentage", style="green")
        tech_table.add_column("Bytes", style="blue")
        
        for tech in repo_data['tech_stack']:
            tech_table.add_row(
                tech['language'],
                f"{tech['percentage']:.1f}%",
                str(tech['bytes'])
            )
        console.print(tech_table)
        
        # Create language distribution pie chart
        plt.figure(figsize=(10, 6))
        plt.pie(
            [tech['percentage'] for tech in repo_data['tech_stack']],
            labels=[tech['language'] for tech in repo_data['tech_stack']],
            autopct='%1.1f%%'
        )
        plt.title('Technology Stack Distribution')
        plt.axis('equal')
        plt.savefig('technology_stack.png')
        plt.close()
        console.print("\n[bold green]Technology stack chart saved as 'technology_stack.png'[/bold green]")
    
    # Display contributors
    if repo_data['contributors']:
        contrib_table = Table(title="\nTop Contributors")
        contrib_table.add_column("Contributor", style="cyan")
        contrib_table.add_column("Commits", style="green")
        
        for contrib in repo_data['contributors'][:10]:  # Show top 10 contributors
            contrib_table.add_row(contrib['name'], str(contrib['commits']))
        console.print(contrib_table)

def main():
    """Main function to run the GitHub repository analyzer."""
    console.print(Panel.fit(
        "[bold green]Advanced GitHub Repository Analyzer[/bold green]\n"
        "Enter a GitHub repository URL to analyze its statistics and get insights.\n"
        "This tool provides detailed analysis including health scores, sentiment analysis,\n"
        "visualizations, and automated reports.",
        title="Welcome"
    ))
    
    while True:
        repo_url = console.input("\n[bold cyan]Enter GitHub repository URL (or 'q' to quit):[/bold cyan] ")
        
        if repo_url.lower() == 'q':
            break
            
        repo_data = analyze_repository(repo_url)
        if repo_data:
            console.print(f"\n[bold green]Analysis complete![/bold green]")
            
        console.print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main() 