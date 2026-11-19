from dataclasses import dataclass


@dataclass
class Record:
    provision_title: str
    document_name: str
    section_or_rule: str
    plain_summary: str
    who_it_helps: str
    source_url: str
