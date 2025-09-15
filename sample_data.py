from app import app, db, NewsArticle, Post
from datetime import datetime

def add_sample_data():
    with app.app_context():
        # Add sample news articles
        if NewsArticle.query.count() == 0:
            news_articles = [
                NewsArticle(
                    title="Latest Innovations in Smart HVAC Systems Drive Energy Efficiency",
                    description="New smart thermostats and AI-powered HVAC controls are revolutionizing home climate management, reducing energy costs by up to 30%.",
                    link="https://example.com/smart-hvac",
                    pub_date=datetime(2024, 9, 10, 10, 30),
                    source_id="HVAC Industry Today",
                    image_url="https://images.unsplash.com/photo-1621905251918-48416bd8575a?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
                    api_source="manual"
                ),
                NewsArticle(
                    title="Solar Panel Efficiency Reaches Record High in 2024",
                    description="Breakthrough in perovskite solar cell technology promises to make solar installations more affordable and efficient than ever before.",
                    link="https://example.com/solar-efficiency",
                    pub_date=datetime(2024, 9, 8, 14, 15),
                    source_id="Solar Power World",
                    image_url="https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80",
                    api_source="manual"
                ),
                NewsArticle(
                    title="New Refrigeration Standards Set to Reduce Environmental Impact",
                    description="Updated EPA regulations for commercial refrigeration systems focus on reducing greenhouse gas emissions and improving energy efficiency.",
                    link="https://example.com/refrigeration-standards",
                    pub_date=datetime(2024, 9, 5, 9, 45),
                    source_id="Refrigeration & AC Today",
                    image_url="https://images.unsplash.com/photo-1595674057936-9891f1bb4cb6?auto=format&fit=crop&w=400&q=80",
                    api_source="manual"
                ),
                NewsArticle(
                    title="Electric Vehicle Charging Infrastructure Expands Rapidly",
                    description="Residential EV charging installations surge as more homeowners adopt electric vehicles, creating new opportunities for electrical contractors.",
                    link="https://example.com/ev-charging",
                    pub_date=datetime(2024, 9, 3, 16, 20),
                    source_id="Electrical Contractor",
                    image_url="https://images.unsplash.com/photo-1518837695005-2083093ee35b?auto=format&fit=crop&w=400&q=80",
                    api_source="manual"
                )
            ]

            for article in news_articles:
                db.session.add(article)

        # Add sample posts
        if Post.query.count() == 0:
            posts = [
                Post(
                    title="Complete AC System Installation",
                    content="Professional installation of a high-efficiency air conditioning system for a residential property. Included ductwork, electrical connections, and system testing. The installation was completed on time and within budget, ensuring optimal cooling performance for the client.",
                    image_url="https://images.unsplash.com/photo-1503389152951-9c3c317b99c7?auto=format&fit=crop&w=400&q=80",
                    category="HVAC",
                    post_type="portfolio",
                    published=True
                ),
                Post(
                    title="Solar Panel System Maintenance",
                    content="Comprehensive maintenance service for a 10kW residential solar panel system. Performed cleaning, electrical testing, inverter diagnostics, and performance optimization. System efficiency improved by 15% after maintenance.",
                    image_url="https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80",
                    category="Solar",
                    post_type="portfolio",
                    published=True
                ),
                Post(
                    title="Commercial Refrigeration Repair",
                    content="Emergency repair service for a commercial walk-in freezer. Diagnosed and replaced faulty compressor, repaired evaporator coils, and restored proper temperature control. Business operations resumed within 4 hours.",
                    image_url="https://images.unsplash.com/photo-1595674057936-9891f1bb4cb6?auto=format&fit=crop&w=400&q=80",
                    category="Refrigeration",
                    post_type="portfolio",
                    published=True
                ),
                Post(
                    title="Whole House Electrical Rewiring",
                    content="Complete electrical system upgrade for a 3-bedroom home. Replaced outdated wiring, installed new circuit breakers, added GFCI outlets, and upgraded to modern electrical standards. All work passed final inspection.",
                    image_url="https://images.unsplash.com/photo-1518837695005-2083093ee35b?auto=format&fit=crop&w=400&q=80",
                    category="Electrical",
                    post_type="portfolio",
                    published=True
                ),
                Post(
                    title="Used Inverter for Sale - 5kVA",
                    content="High-quality 5kVA inverter available for sale. Features include pure sine wave output, LCD display, automatic voltage regulation, and battery charging capability. Perfect for home backup power or small business use.",
                    image_url="https://images.unsplash.com/photo-1518837695005-2083093ee35b?auto=format&fit=crop&w=400&q=80",
                    category="Power Systems",
                    post_type="sale",
                    price=450000.00,
                    currency="NGN",
                    negotiable=True,
                    item_link="https://wa.me/2349033150460?text=Hi! I'm interested in the 5kVA inverter",
                    published=True
                ),
                Post(
                    title="Solar Inverter - Brand New",
                    content="Professional-grade 3kW solar inverter with MPPT charge controller. Compatible with all major solar panel brands, includes LCD display, and comes with 2-year warranty. Ideal for off-grid solar installations.",
                    image_url="https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80",
                    category="Solar Equipment",
                    post_type="sale",
                    price=250000.00,
                    currency="NGN",
                    negotiable=False,
                    item_link="https://wa.me/2349033150460?text=Hi! I'm interested in the 3kW solar inverter",
                    published=True
                ),
                Post(
                    title="Commercial AC Unit - 2 Ton",
                    content="Commercial-grade air conditioning unit, 2-ton capacity. Perfect for small offices or retail spaces. Energy-efficient with remote control and programmable timer. Recently serviced and in excellent condition.",
                    image_url="https://images.unsplash.com/photo-1503389152951-9c3c317b99c7?auto=format&fit=crop&w=400&q=80",
                    category="HVAC Equipment",
                    post_type="sale",
                    price=180000.00,
                    currency="NGN",
                    negotiable=True,
                    item_link="https://wa.me/2349033150460?text=Hi! I'm interested in the 2-ton AC unit",
                    published=True
                )
            ]

            for post in posts:
                db.session.add(post)

        db.session.commit()
        print("Sample data added successfully!")

if __name__ == "__main__":
    add_sample_data()