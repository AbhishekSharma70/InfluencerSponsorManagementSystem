from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()

class Admin(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(80),unique=True,nullable=False)
    password=db.Column(db.String(80),nullable=False)
   
class Sponsor(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(80),unique=True,nullable=False)
    password=db.Column(db.String(80),nullable=False)
    industry=db.Column(db.String(120),nullable=False)
    flagged=db.Column(db.Boolean,default=False)

class Influencer(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(80),unique=True,nullable=False)
    password=db.Column(db.String(80),nullable=False)
    platform_presence=db.Column(db.String(120),nullable=False)
    flagged=db.Column(db.Boolean,default=False)
    ad_requests=db.relationship('AdRequest',backref='influencer',lazy=True)

class SponsorProfile(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    sponsor_id=db.Column(db.Integer,db.ForeignKey('sponsor.id'),nullable=False)
    company_name=db.Column(db.String(120),nullable=False)
    industry=db.Column(db.String(120),nullable=True)
    budget=db.Column(db.Float,nullable=True)

class InfluncerProfile(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    influencer_id=db.Column(db.Integer,db.ForeignKey('influencer.id'),nullable=False)
    name=db.Column(db.String(120),nullable=False)
    category=db.Column(db.String(120),nullable=False)
    niche=db.Column(db.String(120),nullable=True)
    reach=db.Column(db.Integer,nullable=True)


class Campaign(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    sponsor_id=db.Column(db.Integer,db.ForeignKey('sponsor.id'),nullable=False)
    name=db.Column(db.String(120),nullable=False)
    description=db.Column(db.Text,nullable=True)
    start_date=db.Column(db.Date,nullable=False)
    end_date=db.Column(db.Date,nullable=False)
    budget=db.Column(db.Float,nullable=False)
    visibility=db.Column(db.String(10),nullable=False)
    goals=db.Column(db.Text,nullable=True)
    niche=db.Column(db.String(120),nullable=True)
    ad_requests=db.relationship('AdRequest',backref='campaign',lazy=True)
    
class AdRequest(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    campaign_id=db.Column(db.Integer,db.ForeignKey('campaign.id'),nullable=False)
    influencer_id=db.Column(db.Integer,db.ForeignKey('influencer.id'),nullable=False)
    messages=db.Column(db.Text,nullable=False)
    requirements=db.Column(db.Text,nullable=False)
    payment_amount=db.Column(db.Float,nullable=False)
    status=db.Column(db.String(10),nullable=False)
    payment_status=db.Column(db.Boolean,default=False)

    @property
    def influencer_username(self):
        return self.influencer.username
    
    @property
    def campaign_name(self):
        return self.campaign.name

    