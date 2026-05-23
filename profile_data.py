# Pre-seeded profile data from Khala's resume
# Populated once on first run — edit via /profile in the dashboard

PROFILE_INFO = {
    'full_name':  'Khala Wright',
    'location':   'Cleveland Heights, OH',
    'linkedin':   'linkedin.com/in/khala-wright-3662b2266',
    'github':     'github.com/khalathecoder',
    'email':      '',   # fill in .env or profile page
    'phone':      '',   # fill in profile page
    'website':    '',
}

SUMMARIES = {
    'A': (
        "Security analyst and detection engineer with 3+ years investigating application security events, "
        "remediating IAM and access control violations, and enforcing compliance controls in Azure-hosted "
        "HIPAA-regulated environments. Holds M.S. Cybersecurity & Information Assurance (WGU, 2026), "
        "CompTIA CySA+ and PenTest+. Built DataPulse, a production DSPM tool integrating Wazuh 4.7 SIEM "
        "for real-time alert correlation and HIPAA Technical Safeguard violation scanning."
    ),
    'B': (
        "Production Support Engineer and security-focused developer with 3+ years supporting enterprise "
        ".NET/C# applications in Azure-hosted, regulated healthcare environments. Holds M.S. Cybersecurity "
        "& Information Assurance (WGU, 2026), CompTIA CySA+ and PenTest+. Proven ability to own incidents "
        "end-to-end, build internal tooling, and communicate technical findings to non-technical stakeholders."
    ),
}

EXPERIENCE = [
    {
        'resume': 'A',
        'title':   'Security Operations Engineer',
        'company': 'Solventum (formerly 3M Health)',
        'start':   '01/2024',
        'end':     'Present',
        'bullets': [
            "Investigate application security events including IAM misconfigurations, access control violations, and anomalous data access patterns across Azure-hosted HIPAA-regulated environments",
            "Perform threat detection and log analysis using KQL across Azure Monitor and Application Insights, identifying security regressions and behavioral anomalies before they impact production systems",
            "Remediate credential exposure, secrets mismanagement, and privilege escalation risks in multi-environment Azure deployments — dev, test, and production",
            "Build PowerShell, Bash, and Python security automation scripts that reduce mean time to detect (MTTD) and eliminate repetitive diagnostic toil across recurring incident patterns",
            "Conduct forensic SQL and LINQPad investigations against production schemas to validate data integrity and support compliance with HIPAA Technical Safeguard requirements (45 CFR §164.312)",
            "Enforce security controls and configuration hygiene across IIS and Azure App Services deployments, supporting release readiness and post-deployment security validation",
            "Facilitate daily scrum and biweekly sprint review and planning ceremonies, coordinating cross-functional priorities and driving delivery cadence",
            "Manage NuGet package dependency updates across production .NET applications, remediating known CVEs in third-party packages as part of release readiness validation",
        ],
    },
    {
        'resume': 'B',
        'title':   'Production Support Engineer',
        'company': 'Solventum (formerly 3M Health)',
        'start':   '01/2024',
        'end':     'Present',
        'bullets': [
            "Support production C#/.NET healthcare applications deployed across Azure App Services and IIS",
            "Monitor application health via Azure Application Insights and KQL log queries; identify performance regressions before they impact end users",
            "Investigate and resolve deployment failures, misconfigured access controls, and data integrity issues across Azure SQL and SQL Server environments",
            "Build and maintain PowerShell, Bash, and Python automation scripts that eliminate repetitive diagnostics, reducing investigation time across production incidents",
            "Perform LINQPad and SQL investigations against domain-specific schemas to validate production data fixes and support release readiness",
            "Apply security-aware practices when handling credentials, access controls, and configuration values in regulated HIPAA environments",
            "Facilitate daily scrum and biweekly sprint review and planning ceremonies for the engineering team",
            "Manage NuGet package dependency updates across production .NET applications as part of release cycle maintenance",
        ],
    },
    {
        'resume': 'A',
        'title':   'Security-Focused Support Engineer',
        'company': '3M Health',
        'start':   '06/2023',
        'end':     '01/2024',
        'bullets': [
            "Performed log analysis and security triage across Azure-hosted multi-tenant SaaS environments, isolating application-layer and data-layer security issues",
            "Investigated authentication failures, session anomalies, and API misbehavior in production portals — implementing event-driven fixes to prevent unauthorized or premature data access",
            "Supported incident response workflows and maintenance windows; produced resolution documentation and runbooks to build repeatable security response procedures",
        ],
    },
    {
        'resume': 'B',
        'title':   'Production Support Engineer',
        'company': '3M Health',
        'start':   '06/2023',
        'end':     '01/2024',
        'bullets': [
            "Provided Tier 2/Tier 3 support for enterprise applications hosted on Azure, supporting a dental-focused SaaS platform",
            "Performed log analysis and SQL queries to isolate application and data-layer issues in multi-tenant environments",
            "Debugged Kendo UI grid and AJAX validation issues in production portals, implementing event-driven cancellation patterns to prevent premature API calls",
            "Supported scheduled releases, maintenance windows, and incident response workflows; documented resolution steps to build team-wide runbooks",
        ],
    },
    {
        'resume': 'both',
        'title':   'Team Lead / HIPAA Compliance Specialist',
        'company': 'iScriptServices',
        'start':   '03/2021',
        'end':     '06/2023',
        'bullets': [
            "Oversaw HIPAA-compliant medical documentation workflows across 15+ remote team members, enforcing data privacy requirements and PHI handling controls in high-volume clinical environments",
            "Served as escalation point for data accuracy, access, and compliance issues across Epic, Cerner/Oracle Health, Meditech, NextGen, McKesson, AthenaHealth, Allscripts, and eClinicalWorks",
        ],
    },
]

EDUCATION = [
    {
        'degree':  'M.S. Cybersecurity & Information Assurance',
        'school':  'Western Governors University (WGU)',
        'date':    '05/2026',
    },
]

SKILLS = {
    'A': {
        'Cloud & DevOps':  'Microsoft Azure, App Services, Application Insights, KQL, IIS, CI/CD',
        'Languages':       'C#, Python, PowerShell, Bash, SQL, JavaScript',
        'Frameworks':      '.NET / ASP.NET Core, Blazor, EF Core, Flask',
        'Databases':       'SQL Server, Azure SQL, SQLite, PostgreSQL',
        'Security':        'CyberArk PAM, Microsoft Sentinel, Tenable/Nessus, Defender for Endpoint, Wazuh SIEM, SailPoint (IIQ), Entra ID, DSPM/DLP',
        'Networking':      'TCP/IP, DNS, HTTP/S, TLS, SSH, IAM',
        'Platforms':       'ServiceNow, Salesforce, Okta, SailPoint, Windows, Linux (Ubuntu, Kali)',
        'Tools':           'Git/GitHub, LINQPad, Visual Studio, VS Code, Kali Linux, WSL, TryHackMe, Burp Suite',
    },
    'B': {
        'Cloud & DevOps':  'Microsoft Azure, App Services, Application Insights, KQL, IIS, CI/CD',
        'Languages':       'C#, Python, PowerShell, Bash, SQL, JavaScript, TypeScript',
        'Frameworks':      '.NET / ASP.NET Core, Blazor, EF Core, Flask, Angular',
        'Databases':       'SQL Server, Azure SQL, SQLite, PostgreSQL',
        'Security':        'CyberArk PAM, Microsoft Sentinel, Tenable/Nessus, Defender for Endpoint, Wazuh SIEM, SailPoint (IIQ), Entra ID',
        'Networking':      'TCP/IP, DNS, HTTP/S, TLS, SSH, IAM',
        'Platforms':       'ServiceNow, Salesforce, Okta, SailPoint, Windows, Linux (Ubuntu, Kali)',
        'Tools':           'Git/GitHub, LINQPad, Visual Studio, VS Code, Kali Linux, WSL, TryHackMe',
    },
}

CERTIFICATIONS = [
    'CompTIA CySA+',
    'CompTIA PenTest+ (PT0-003)',
]
