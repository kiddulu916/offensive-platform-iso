"""
Database models and initialization
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from app.core.config import settings

Base = declarative_base()

# Association tables for many-to-many relationships
subdomain_ip_association = Table(
    'subdomain_ip_association',
    Base.metadata,
    Column('subdomain_id', Integer, ForeignKey('subdomains.id')),
    Column('ip_id', Integer, ForeignKey('ips.id'))
)

subdomain_asn_association = Table(
    'subdomain_asn_association',
    Base.metadata,
    Column('subdomain_id', Integer, ForeignKey('subdomains.id')),
    Column('asn_id', Integer, ForeignKey('asns.id'))
)

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    scans = relationship("Scan", back_populates="user")

class Scan(Base):
    """Scan/Workflow execution model"""
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    workflow_name = Column(String(100), nullable=False)
    target = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    results = Column(Text)  # JSON string
    report_path = Column(String(500))
    
    # Relationships
    user = relationship("User", back_populates="scans")
    tasks = relationship("Task", back_populates="scan")

class Task(Base):
    """Individual task execution model"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    task_name = Column(String(100), nullable=False)
    tool = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    output = Column(Text)  # JSON string
    errors = Column(Text)

    # Relationships
    scan = relationship("Scan", back_populates="tasks")

class Subdomain(Base):
    """Subdomain model - tracks discovered subdomains"""
    __tablename__ = "subdomains"

    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    name = Column(String(255), nullable=False)
    source = Column(String(50))  # Tool that discovered it (amass, subfinder, etc.)
    discovered_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    scan = relationship("Scan")
    ips = relationship("IP", secondary=subdomain_ip_association, back_populates="subdomains")
    asns = relationship("ASN", secondary=subdomain_asn_association, back_populates="subdomains")

class IP(Base):
    """IP address model - tracks IP addresses"""
    __tablename__ = "ips"

    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    address = Column(String(45), nullable=False)  # Support IPv4 and IPv6
    discovered_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    scan = relationship("Scan")
    subdomains = relationship("Subdomain", secondary=subdomain_ip_association, back_populates="ips")
    ports = relationship("Port", back_populates="ip")

class Port(Base):
    """Port model - tracks open ports on IPs"""
    __tablename__ = "ports"

    id = Column(Integer, primary_key=True)
    ip_id = Column(Integer, ForeignKey("ips.id"))
    scan_id = Column(Integer, ForeignKey("scans.id"))
    port_number = Column(Integer, nullable=False)
    protocol = Column(String(10), default="tcp")  # tcp, udp
    service = Column(String(100))  # Service name (http, ssh, etc.)
    version = Column(String(255))  # Service version
    state = Column(String(20), default="open")  # open, closed, filtered
    discovered_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    scan = relationship("Scan")
    ip = relationship("IP", back_populates="ports")

class ASN(Base):
    """ASN model - tracks Autonomous System Numbers"""
    __tablename__ = "asns"

    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    asn_number = Column(String(20), nullable=False)  # e.g., "AS12345"
    organization = Column(String(255))  # Organization name
    discovered_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    scan = relationship("Scan")
    subdomains = relationship("Subdomain", secondary=subdomain_asn_association, back_populates="asns")

# Create engine and session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_database():
    """Initialize database"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def migrate_existing_scans():
    """
    Migrate existing scan data to new table structure.
    Parses JSON results from existing scans and populates new relational tables.
    """
    import json
    from pathlib import Path

    db = SessionLocal()

    try:
        # Get all scans with results
        scans = db.query(Scan).filter(Scan.results.isnot(None)).all()

        for scan in scans:
            try:
                # Parse results JSON
                results = json.loads(scan.results) if isinstance(scan.results, str) else scan.results

                # Also try to read from subdomains.json file if it exists
                domain = scan.target.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
                subdomains_file = Path("data/scans") / domain / "final" / "subdomains.json"

                subdomain_data = []

                # Try to load from file first (more complete data)
                if subdomains_file.exists():
                    with open(subdomains_file, 'r') as f:
                        subdomain_data = json.load(f)
                else:
                    # Fallback to parsing from task results
                    for task_id, task_result in results.items():
                        if isinstance(task_result, dict) and "output" in task_result:
                            output = task_result["output"]
                            if "subdomains" in output:
                                subdomain_data.extend(output["subdomains"])
                            elif "merged_data" in output:
                                subdomain_data.extend(output["merged_data"])

                # Process subdomain data
                if subdomain_data:
                    _process_subdomain_data(db, scan.id, subdomain_data)

                db.commit()
                print(f"Migrated scan {scan.id}: {scan.workflow_name} - {scan.target}")

            except Exception as e:
                print(f"Error migrating scan {scan.id}: {e}")
                db.rollback()
                continue

        print("Migration completed successfully")

    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

def _process_subdomain_data(db, scan_id, subdomain_data):
    """Helper function to process subdomain data and populate tables"""

    for item in subdomain_data:
        if not isinstance(item, dict):
            continue

        subdomain_name = item.get("name")
        if not subdomain_name:
            continue

        # Check if subdomain already exists for this scan
        existing_subdomain = db.query(Subdomain).filter(
            Subdomain.scan_id == scan_id,
            Subdomain.name == subdomain_name
        ).first()

        if existing_subdomain:
            subdomain = existing_subdomain
        else:
            # Create subdomain
            subdomain = Subdomain(
                scan_id=scan_id,
                name=subdomain_name,
                source=item.get("source", "unknown")
            )
            db.add(subdomain)
            db.flush()  # Get the subdomain ID

        # Process IPs
        ips = item.get("ips", [])
        if not isinstance(ips, list):
            ips = [ips] if ips else []

        for ip_addr in ips:
            if not ip_addr:
                continue

            # Check if IP already exists for this scan
            existing_ip = db.query(IP).filter(
                IP.scan_id == scan_id,
                IP.address == ip_addr
            ).first()

            if existing_ip:
                ip_obj = existing_ip
            else:
                ip_obj = IP(
                    scan_id=scan_id,
                    address=ip_addr
                )
                db.add(ip_obj)
                db.flush()

            # Associate subdomain with IP
            if ip_obj not in subdomain.ips:
                subdomain.ips.append(ip_obj)

        # Process ASNs
        asns = item.get("asns", [])
        if not isinstance(asns, list):
            asns = [asns] if asns else []

        for asn_num in asns:
            if not asn_num:
                continue

            # Check if ASN already exists for this scan
            existing_asn = db.query(ASN).filter(
                ASN.scan_id == scan_id,
                ASN.asn_number == asn_num
            ).first()

            if existing_asn:
                asn_obj = existing_asn
            else:
                asn_obj = ASN(
                    scan_id=scan_id,
                    asn_number=asn_num
                )
                db.add(asn_obj)
                db.flush()

            # Associate subdomain with ASN
            if asn_obj not in subdomain.asns:
                subdomain.asns.append(asn_obj)

        # Process ports
        ports = item.get("ports", {})
        if isinstance(ports, dict):
            for port_num, service_desc in ports.items():
                # Find the IP object for this subdomain
                for ip_obj in subdomain.ips:
                    # Check if port already exists
                    existing_port = db.query(Port).filter(
                        Port.ip_id == ip_obj.id,
                        Port.port_number == int(port_num)
                    ).first()

                    if not existing_port:
                        # Parse service description
                        service_parts = service_desc.split(" ", 1)
                        service_name = service_parts[0] if service_parts else service_desc
                        service_version = service_parts[1] if len(service_parts) > 1 else ""

                        port_obj = Port(
                            ip_id=ip_obj.id,
                            scan_id=scan_id,
                            port_number=int(port_num),
                            service=service_name,
                            version=service_version,
                            state="open"
                        )
                        db.add(port_obj)