from flask import Flask,render_template,redirect,url_for,session,flash,request
from models import db, Admin, Sponsor, Influencer, SponsorProfile, InfluncerProfile, Campaign, AdRequest
from datetime import datetime
from instamojo_wrapper import Instamojo

app=Flask(__name__)
app.secret_key='supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///app2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db.init_app(app)

with app.app_context():
    db.create_all()

API_KEY='test_8a62048702432ca1a1d3de7e793'
AUTH_TOKEN='test_75b8480ad24b46823ad1c5d07af'

api=Instamojo(api_key=API_KEY,auth_token=AUTH_TOKEN,endpoint='https://test.instamojo.com/api/1.1/')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        role=request.form['role']
        industry=request.form.get('industry')
        platform_presence=request.form.get('platform_presence')

        existing_user=None
        if role=='Sponsor':
            existing_user=Sponsor.query.filter_by(username=username).first()
        elif role=='Influencer':
            existing_user=Influencer.query.filter_by(username=username).first()
        else:
            existing_user=Admin.query.filter_by(username=username).first()

        if existing_user:
            flash('Username already exists. Please choose another option')
            return redirect(url_for('signup'))
        
        if role=='Sponsor':
            new_user=Sponsor(username=username,password=password,industry=industry)
        elif role=='Influencer':
            new_user=Influencer(username=username,password=password,platform_presence=platform_presence)
        else:
            new_user=Admin(username=username,password=password)
        
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully')
        return redirect(url_for('index'))
    
    return render_template('signup.html')


@app.route('/admin/login',methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']

        found_user=Admin.query.filter_by(username=username).first()
        if found_user and found_user.password==password:
            session['username']=found_user.username
            session['role']='Admin'
            flash('Login Successfully')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('User not found')
            return redirect(url_for('admin_login'))
    
    if 'username' in session:
        return redirect(url_for('admin_dashboard'))
                        
    return render_template('admin_login.html')

@app.route('/sponsor/login',methods=['GET','POST'])
def sponsor_login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        industry=request.form['industry']

        found_user=Sponsor.query.filter_by(username=username).first()
        if found_user and found_user.password==password:
            session['username']=found_user.username
            session['role']='Sponsor'
            session['industry']=found_user.industry
            flash('Login Successfully')
            return redirect(url_for('sponsor_dashboard'))
        else:
            flash('User not found')
            return redirect(url_for('sponsor_login'))
    
    if 'username' in session:
        return redirect(url_for('sponsor_dashboard'))
    
    return render_template('sponsor_login.html')

@app.route('/influencer/login',methods=['GET','POST'])
def influencer_login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        platform_presence=request.form['platform_presence']

        found_user=Influencer.query.filter_by(username=username).first()
        if found_user and found_user.password==password:
            session['username']=found_user.username
            session['role']='Influencer'
            session['platform_presence']=found_user.platform_presence
            flash('Login Successfully')
            return redirect(url_for('influencer_dashboard'))
        else:
            flash('User not found')
            return redirect(url_for('influencer_login'))
    
    if 'username' in session:
        return redirect(url_for('influencer_dashboard'))
    
    return render_template('influencer_login.html')

@app.route('/logout')
def logout():
    session.pop('username',None)
    session.pop('role',None)
    session.pop('industry',None)
    session.pop('platform_presence',None)
    flash('You have been logged out successfully')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'username' not in session or session['role']!='Admin':
        return redirect(url_for('admin_login'))
    else:
        active_users={
            'sponsors':Sponsor.query.count(),
            'influencers':Influencer.query.count(),
            'admins':Admin.query.count()
        }
        campaigns={
            'public':Campaign.query.filter_by(visibility='public').count(),
            'private':Campaign.query.filter_by(visibility='private').count(),
            'total':Campaign.query.count()
        }
        ad_requests={
            'pending':AdRequest.query.filter_by(status='Pending').count(),
            'accepted':AdRequest.query.filter_by(status='Accepted').count(),
            'rejected':AdRequest.query.filter_by(status='rejected').count(),
            'total':AdRequest.query.count()
        }
        
        flagged_users={
            'sponsors':Sponsor.query.filter_by(flagged=False).count(),
            'influencers':Sponsor.query.filter_by(flagged=False).count()
        }
        return render_template('admin_dashboard.html',active_users=active_users,campaigns=campaigns,ad_requests=ad_requests,flagged_users=flagged_users)
    
@app.route('/admin/users')
def admin_users():
    if 'username' not in session or session['role']!='Admin':
        return redirect(url_for('admin_login'))
    
    sponsors=Sponsor.query.all()
    influencers=Influencer.query.all()
    return render_template('admin_users.html',sponsors=sponsors,influencers=influencers)

@app.route('/admin/flag_user/<string:user_type>/<int:user_id>',methods=['POST'])
def flag_user(user_type,user_id):
    if 'username' not in session or session['role']!='Admin':
        return redirect(url_for('admin_login'))
    
    if user_type == 'sponsor':
        user=Sponsor.query.get_or_404(user_id)
    elif user_type == 'influencer':
        user=Influencer.query.get_or_404(user_id)
    else:
        flash('Invalid user type')
        return redirect(url_for('admin_users'))
    
    user.flagged=not user.flagged
    db.session.commit()
    flash(f'{user.username} flag status changed')
    return redirect(url_for('admin_dashboard'))
    
@app.route('/sponsor/dashboard')
def sponsor_dashboard():
    if 'username' not in session or session.get('role')!='Sponsor':
        return redirect(url_for('sponsor_login'))
    else:
        sponsor=Sponsor.query.filter_by(username=session['username']).first()
        profile=SponsorProfile.query.filter_by(sponsor_id=sponsor.id).first()
        campaigns=Campaign.query.filter_by(sponsor_id=sponsor.id).first()
        campaigns_with_ads=[]
        campaigns_ads=Campaign.query.filter_by(sponsor_id=sponsor.id).all()
        for campaign in campaigns_ads:
            ad_requests=AdRequest.query.filter_by(campaign_id=campaign.id).all()
            campaigns_with_ads.append((campaign,ad_requests))
        return render_template('sponsor_dashboard.html',sponsor=sponsor,profile=profile,campaigns=campaigns,campaigns_with_ads=campaigns_with_ads)
    
@app.route('/sponsor/update_profile',methods=['GET','POST'])
def sponsor_update_profile():
    if 'username' not in session or session.get('role')!='Sponsor':
        return redirect(url_for('sponsor_login'))
    else:
        sponsor=Sponsor.query.filter_by(username=session['username']).first()
        profile=SponsorProfile.query.filter_by(sponsor_id=sponsor.id).first()
        if request.method=="POST":
            company_name=request.form['company_name']
            industry=request.form['industry']
            budget=request.form['budget']

            if profile:
                profile.company_name=company_name
                profile.industry=industry
                profile.budget=budget
            else:
                new_profile=SponsorProfile(sponsor_id=sponsor.id,company_name=company_name,industry=industry,budget=budget)
                db.session.add(new_profile)
                db.session.commit()
                flash("Profile updated successfully")
                return redirect(url_for('sponsor_dashboard'))
        
        return render_template('sponsor_update_profile.html',profile=profile)
    
@app.route('/sponsor/create_campaign',methods=['GET','POST'])
def create_campaign():
    if 'username' not in session or session['role']!='Sponsor':
        return redirect(url_for('sponsor_login'))    
    else:
        sponsor=Sponsor.query.filter_by(username=session['username']).first()
        if  sponsor.flagged:
            flash('You are flagged and cannot create a campaign')
            return redirect(url_for('sponsor_dashboard'))
        else:
            if request.method=="POST":
             name=request.form['name']
             description=request.form['name']
             start_date=datetime.strptime(request.form['start_date'],'%Y-%m-%d')
             end_date=datetime.strptime(request.form['end_date'],'%Y-%m-%d')
             budget=request.form['budget']
             visibility=request.form['visibility']
             goals=request.form['goals']
             niche=request.form['niche']
             campaign=Campaign(sponsor_id=sponsor.id,name=name,description=description,start_date=start_date,end_date=end_date,budget=budget,visibility=visibility,goals=goals)
             db.session.add(campaign)
             db.session.commit()
             flash('Campaign created successfully')
             return redirect(url_for('sponsor_dashboard'))
        return render_template('create_campaign.html')

@app.route('/create_ad_request',methods=['GET','POST'])
def create_ad_request():
    if 'username' not in session or session['role']!='Sponsor':
        return redirect(url_for('sponsor_login'))
    
    sponsor=Sponsor.query.filter_by(username=session['username']).first()
    if sponsor.flagged:
        flash('You are flagged and cannot create an ad request')
        return redirect(url_for('sponsor_dashboard'))
    else:

     if request.method=='POST':
        campaign_id=request.form['campaign_id']
        influencer_id=request.form['influencer_id']
        messages=request.form['messages']
        requirements=request.form['requirements']
        payment_amount=request.form['payment_amount']
        status=request.form['status']

        new_ad_request=AdRequest(campaign_id=campaign_id,influencer_id=influencer_id,messages=messages,requirements=requirements,payment_amount=payment_amount,status=status)
        db.session.add(new_ad_request)
        db.session.commit()
        flash('Ad requested succesfully')
        return redirect(url_for('sponsor_dashboard'))
    
     influencers=Influencer.query.all()
     campaigns=Campaign.query.all()
     return render_template('create_ad_request.html',campaigns=campaigns,influencers=influencers)
            
@app.route('/influencer/dashboard')
def influencer_dashboard():
    if 'username' not in session or session['role']!='Influencer':
        return redirect(url_for('influencer_login'))
    else:
        influencer=Influencer.query.filter_by(username=session['username']).first()
        profile=InfluncerProfile.query.filter_by(influencer_id=influencer.id).first()
        ad_requests=AdRequest.query.filter_by(influencer_id=influencer.id).all()
        return render_template('influencer_dashboard.html',influencer=influencer,profile=profile,ad_requests=ad_requests)
    
@app.route('/influencer/update_profile',methods=['GET','POST'])
def influencer_update_profile():
    if 'username' not in session or session.get('role')!='Influencer':
        return redirect(url_for('influencer_login'))
    else:
        influencer=Influencer.query.filter_by(username=session['username']).first()
        profile=InfluncerProfile.query.filter_by(influencer_id=influencer.id).first()
        if request.method=="POST":
          name=request.form['name']
          category=request.form['category']
          niche=request.form['niche']
          reach=request.form['reach']

          if profile:
            profile.name=name
            profile.category=category
            profile.niche=niche
            profile.reach=reach
          else:
            new_profile=InfluncerProfile(influencer_id=influencer.id,name=name,category=category,niche=niche,reach=reach)
            db.session.add(new_profile)
            db.session.commit()
            flash("Profile updated successfully")
            return redirect(url_for('influencer_dashboard'))
          
        return render_template('influencer_update_profile.html',profile=profile)
        
@app.route('/ad_request/<int:ad_request_id>/update_status',methods=['POST'])
def update_ad_request_status(ad_request_id):
    if 'username' not in session or session.get('role')!='Influencer':
        return redirect(url_for('influencer_login'))
    
    influencer=Influencer.query.filter_by(username=session['username']).first()

    if  influencer.flagged:
        flash('You are flagged and cannot update ad request status')
        return redirect(url_for('influencer_dashboard'))

    else:
        ad_request=AdRequest.query.get(ad_request_id)
        if ad_request and ad_request.influencer_id==Influencer.query.filter_by(username=session['username']).first().id:
            status=request.form.get('status')
            if status in ['Accepted', 'Rejected']:
                ad_request.status=status
                db.session.commit()
                flash(f'Ad request {status.lower()} successfully')
            else:
                flash('Invalid status update')
        else:
            flash('Ad request not found or not authorized')
        return redirect(url_for('influencer_dashboard'))
    
@app.route('/ad_request/<int:ad_request_id>/update_payment',methods=['POST'])
def update_ad_request_payment(ad_request_id):
    if 'username' not in session or session.get('role')!='Influencer':
        return redirect(url_for('influencer_login'))
    
    influencer=Influencer.query.filter_by(username=session['username']).first()

    if  influencer.flagged:
        flash('You are flagged and cannot update ad request payment')
        return redirect(url_for('influencer_dashboard'))

    else:
        ad_request=AdRequest.query.get(ad_request_id)
        if ad_request and ad_request.influencer_id==Influencer.query.filter_by(username=session['username']).first().id:
            payment_amount=float(request.form.get('payment_amount'))
            ad_request.payment_amount=payment_amount
            db.session.commit()
            flash(f'Payment amount updated successfully')
        else:
            flash('Ad request not found or not authorized')
        return redirect(url_for('influencer_dashboard'))
    

    
@app.route('/search_influencers',methods=['GET','POST'])
def all_influencers():
    if 'username' not in session or session['role']!='Sponsor':
        return redirect(url_for('sponsor_login'))
    
    if request.method=='POST':
        niche=request.form.get('niche')
        min_reach=request.form.get('reach')
        query=InfluncerProfile.query

        if niche:
            query=query.filter(InfluncerProfile.niche.ilike(f'%{niche}%'))
        if min_reach:
            query=query.filter(InfluncerProfile.reach>=min_reach)
        influencers=query.all()
        return render_template('search_results.html',results=influencers,type='influencer')
    
    return render_template('search_influencers.html')

    # influencer_profiles=InfluncerProfile.query.all()
    # return render_template('all_influencers.html',influencer_profiles=influencer_profiles)

@app.route('/influencers/sponsor_profiles',methods=['GET','POST'])
def view_sponsor_profiles():
    if 'username' not in session or session['role']!='Influencer':
        return redirect(url_for('influencer_login'))
    
    influencer=Influencer.query.filter_by(username=session['username']).first()
    if influencer.flagged:
        flash('You are flagged and cannot view sponsor profiles')
        return redirect(url_for('influencer_dashboard'))
    else:
        if request.method=='POST':
            try:
                min_budget=float(request.form['budget'])
                query=Campaign.query.filter_by(visibility='public').filter(Campaign.budget>=min_budget)
                campaigns=query.all()
                if not campaigns:
                    flash('No campaigns found with the specified minimum budget')
                    return redirect(url_for('view_sponsor_profiles'))
                else:
                    return render_template('search_results.html',results=campaigns,type='campaign')
            except(ValueError,KeyError) as e:
                flash('Invalid budget value')
                return redirect(url_for('view_sponsor_profiles'))
        return render_template('search_campaigns.html')
            


    # sponsor_profiles=SponsorProfile.query.all()
    # return render_template('view_sponsor_profile.html',sponsor_profiles=sponsor_profiles)

@app.route('/sponsor/delete_ad_request/<int:ad_request_id>',methods=['GET','POST'])
def delete_ad_request(ad_request_id):
    if 'username' not in session or session['role']!='Sponsor':
        return redirect(url_for('sponsor_login'))
    ad_request=AdRequest.query.get_or_404(ad_request_id)
    db.session.delete(ad_request)
    db.session.commit()
    flash('Ad request deleted successfully')
    return redirect(url_for('sponsor_login'))

@app.route('/sponsor/delete_campaign/<int:campaign_id>',methods=['POST'])
def delete_campaign(campaign_id):
    if 'username' not in session or session['role']!='Sponsor':
        return redirect(url_for('sponsor_login'))
    campaign=Campaign.query.get_or_404(campaign_id)
    AdRequest.query.filter_by(campaign_id=campaign.id).delete()
    db.session.delete(campaign)
    db.session.commit()
    flash('Campaign and all assosciated Ad Request deleted successfully')
    return redirect(url_for('sponsor_dashboard'))

@app.route('/sponsor/campaign/<int:campaign_id>/edit',methods=['GET','POST'])
def edit_campaign(campaign_id):
    if 'username' not in session or session['role']!='Sponsor':
        return redirect(url_for('sponsor_login'))
    campaign=Campaign.query.get_or_404(campaign_id)
    if request.method=='POST':
        campaign.name=request.form['name']
        campaign.description=request.form['description']
        campaign.start_date=datetime.strptime(request.form['start_date'],'%Y-%m-%d')
        campaign.end_date=datetime.strptime(request.form['end_date'],'%Y-%m-%d')
        campaign.budget=request.form['budget']
        campaign.visibility=request.form['visibility']
        campaign.goals=request.form['goals']
        campaign.niche=request.form['niche']
        db.session.commit()
        flash('Campaign updated successfully')
        return redirect(url_for('sponsor_dashboard'))
    return render_template('edit_campaign.html',campaign=campaign)

@app.route('/sponsor/ad_request/<int:ad_request_id>/edit',methods=['GET','POST'])
def edit_ad_request(ad_request_id):
    if 'username' not in session or session['role']!='Sponsor':
        return redirect(url_for('sponsor_login'))
    ad_request=AdRequest.query.get_or_404(ad_request_id)
    if request.method=='POST':
        ad_request.messages=request.form['messages']
        ad_request.requirements=request.form['requirements']
        ad_request.payment_amount=request.form['payment_amount']
        ad_request.status=request.form['status']
        db.session.commit()
        return redirect(url_for('sponsor_dashboard'))
    return render_template('edit_ad_request.html',ad_request=ad_request)

@app.route('/influencers/show_campaigns',methods=['GET','POST'])
def show_campaigns():
    if 'username' not in session or session['role']!='Influencer':
        return redirect(url_for('influencer_login'))
    
    influencer=Influencer.query.filter_by(username=session['username']).first()
    if  influencer.flagged:
        flash('You are flagged and cannot view sponsor profiles')
        return redirect(url_for('influencer_dashboard'))
    
    query=Campaign.query.filter(Campaign.visibility=='public')
    if request.method=='POST':
        niche=request.form.get('niche')
        relevance=request.form.get('relevance')

        if niche:
            query=query.filter(Campaign.niche.ilike(f"%{niche}%"))
        if relevance:
            query=query.filter(Campaign.description.ilike(f"%{relevance}"))

        public_campaigns=query.all()
    
        private_campaigns=Campaign.query.join(AdRequest).filter(Campaign.visibility=='private',AdRequest.influencer_id==influencer.id).all()

        if request.method == 'POST' and not public_campaigns:
          flash('No campaigns found matching your criteria')

        return render_template('show_campaigns.html',public_campaigns=public_campaigns,private_campaigns=private_campaigns)
    
    return render_template('show_campaigns.html')

@app.route('/influencer/show_private_campaigns',methods=['GET','POST'])
def show_private_campaigns():

    if 'username' not in session or session['role']!='Influencer':
        return redirect(url_for('influencer_login'))
    
    influencer=Influencer.query.filter_by(username=session['username']).first()
    if  influencer.flagged:
        flash('You are flagged and cannot view sponsor profiles')
        return redirect(url_for('influencer_dashboard'))
    
    private_campaigns=Campaign.query.join(AdRequest).filter(Campaign.visibility=='private',AdRequest.influencer_id==influencer.id).all()

    return render_template('show_private_campaign.html',private_campaigns=private_campaigns)

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/sponsor/ad_request/<int:ad_request_id>/pay',methods=['GET','POST'])
def pay_ad_request(ad_request_id):
    if 'username' not in session or session['role']!='Sponsor':
        return redirect(url_for('sponsor_login'))

    ad_request=AdRequest.query.get_or_404(ad_request_id)
    influencer=ad_request.influencer

    if ad_request.payment_status:
        flash('Payment already made for this ad request')
        return redirect(url_for('sponsor_dashboard'))

    if request.method == 'POST':
        name=request.form['name']
        purpose=request.form['purpose']
        email=request.form['email']
        payment_amount=request.form['payment_amount']

        response=api.payment_request_create(
            amount=payment_amount,
            purpose=purpose,
            buyer_name=name,
            send_email=True,
            email=email,
            redirect_url='http://localhost:5000/success'
        )

        if response['success']:
            ad_request.payment_status=True
            db.session.commit()

        return redirect(response['payment_request']['longurl'])
    
    return render_template('pay_ad_request.html',ad_request=ad_request)

if __name__=="__main":
    app.run(debug=True)