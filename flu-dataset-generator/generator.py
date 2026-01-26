import json
from pathlib import Path
import sys
import zipfile
import yaml
from Bio import Entrez, SeqIO
from dataclasses import dataclass
import click

# Set your email address (required by NCBI)
Entrez.email = "your_email@example.com"

InsdcAccession = str
SequenceName = str

PATHOGEN_TEMPLATE = {
    "alignmentParams": {"minSeedCover": 0.01},
    "schemaVersion": "3.0.0",
    "attributes": {
        "name": "TODO",
        "reference name": "TODO",
        "reference accession": "TODO",
    },
    "files": {
        "reference": "reference.fasta",
        "pathogenJson": "pathogen.json",
        "genomeAnnotation": "genome_annotation.gff3",
    },
}


@dataclass
class Config:
    HA: dict[SequenceName, InsdcAccession]
    NA: dict[SequenceName, InsdcAccession]
    output_dir: str


def fetch_genbank_description(accession: str):
    with Entrez.efetch(
        db="nucleotide",
        id=accession,
        rettype="gb",
        retmode="text",
    ) as handle:
        return SeqIO.read(handle, "genbank").description
    
def generate_dataset(out_dir: Path, ref_name: str, accession: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    fasta_path = out_dir / "reference.fasta"
    gff_path = out_dir / "genome_annotation.gff3"
    pathogen_path = out_dir / "pathogen.json"
    zip_path = out_dir / "dataset.zip"

    try:
        fasta = Entrez.efetch(
            db="nucleotide", id=accession, rettype="fasta", retmode="text"
        )
        fasta_path.write_text(fasta.read())

        gff3 = Entrez.efetch(
            db="nucleotide", id=accession, rettype="gff3", retmode="text"
        )
        gff_path.write_text(gff3.read())

        pathogen_json = PATHOGEN_TEMPLATE.copy()
        pathogen_json["attributes"]["name"] = ref_name
        pathogen_json["attributes"]["reference name"] = fetch_genbank_description(accession)
        pathogen_json["attributes"]["reference accession"] = accession

        pathogen_path.write_text(
            json.dumps(pathogen_json, indent=2, ensure_ascii=False) + "\n"
        )
    except Exception as e:
        print(f" {out_dir} Failed: {e}", file=sys.stderr)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in out_dir.rglob("*"):
            if path == zip_path:
                continue # don’t zip the zip
            zf.write(path, arcname=path.relative_to(out_dir))

def create_datasets(config: Config) -> None:
    for ref_name, accession in config.HA.items():
        out_dir = Path(config.output_dir) / "HA" / ref_name / accession / "unreleased"
        generate_dataset(out_dir, ref_name, accession)
    for ref_name, accession in config.NA.items():
        out_dir = Path(config.output_dir) / "NA" / ref_name / accession / "unreleased"
        generate_dataset(out_dir, ref_name, accession)


@click.command()
@click.option("--config-file", required=True, type=click.Path(exists=True))
def main(config_file: str) -> None:
    with open(config_file, encoding="utf-8") as file:
        full_config = yaml.safe_load(file)
        relevant_config = {key: full_config[key] for key in Config.__annotations__}
        config = Config(**relevant_config)
    create_datasets(config)


if __name__ == "__main__":
    main()
