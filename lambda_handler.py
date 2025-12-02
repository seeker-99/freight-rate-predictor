lambda_handler = '''"""AWS Lambda ETL handler"""
import json
import boto3
import logging
import os
from datetime import datetime
from io import StringIO
import pandas as pd
from src.database.connection import engine, SessionLocal
from src.database.models import Base, Shipment
from src.etl.data_ingestion import FreightDataIngestion
from src.etl.data_cleaning import FreightDataCleaning
from src.models.arima_predictor import ARIMAPredictor

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")

def lambda_handler(event, context):
    """
    Lambda handler for ETL pipeline
    
    Triggered daily via EventBridge
    """
    try:
        logger.info("🚀 Starting ETL pipeline")
        
        # Create database tables
        Base.metadata.create_all(bind=engine)
        
        # 1. Extract data from S3
        logger.info("📥 Extracting data from S3")
        bucket = os.getenv("S3_BUCKET", "freight-rate-data")
        key = "raw/freight_data.csv"
        
        try:
            obj = s3_client.get_object(Bucket=bucket, Key=key)
            df = pd.read_csv(obj["Body"])
            logger.info(f"✅ Extracted {len(df)} records from S3")
        except Exception as e:
            logger.error(f"❌ Failed to read S3: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Data extraction failed"})
            }
        
        # 2. Validate data
        logger.info("🔍 Validating data")
        df, validation_issues = FreightDataIngestion.validate_data(df)
        
        if validation_issues:
            logger.warning(f"⚠️ Validation issues: {validation_issues}")
        
        # 3. Clean data
        logger.info("🧹 Cleaning data")
        df = FreightDataCleaning.clean_data(df)
        
        # 4. Add features
        logger.info("✨ Engineering features")
        df = FreightDataCleaning.add_features(df)
        
        # 5. Load to RDS
        logger.info("💾 Loading to RDS")
        db = SessionLocal()
        
        try:
            # Convert to Shipment records
            shipment_count = 0
            
            for _, row in df.iterrows():
                existing = db.query(Shipment).filter(
                    Shipment.shipment_id == row["shipment_id"]
                ).first()
                
                if not existing:
                    shipment = Shipment(
                        shipment_id=row["shipment_id"],
                        route=row["route"],
                        carrier=row["carrier"],
                        weight_kg=row["weight_kg"],
                        date=pd.to_datetime(row["date"]).date(),
                        rate_per_kg=row["rate_per_kg"],
                        status=row["status"],
                        distance_km=row.get("distance_km"),
                        days_to_delivery=row.get("days_to_delivery")
                    )
                    db.add(shipment)
                    shipment_count += 1
            
            db.commit()
            logger.info(f"✅ Loaded {shipment_count} new shipments to RDS")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to load to RDS: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Data loading failed"})
            }
        finally:
            db.close()
        
        # 6. Train ARIMA models for top routes
        logger.info("🤖 Training ARIMA models")
        
        db = SessionLocal()
        routes = db.query(Shipment.route).distinct().limit(5).all()
        db.close()
        
        model_count = 0
        for (route,) in routes:
            try:
                # Get historical data
                db = SessionLocal()
                shipments = db.query(Shipment).filter(
                    Shipment.route == route
                ).order_by(Shipment.date).all()
                db.close()
                
                if len(shipments) < 30:
                    continue
                
                # Prepare time series
                rates = [s.rate_per_kg for s in shipments]
                dates = [s.date for s in shipments]
                
                # Train model
                predictor = ARIMAPredictor(order=(1, 1, 1))
                if predictor.train(rates, dates):
                    # Generate predictions
                    predictions = predictor.predict(steps=7)
                    
                    # Save predictions to RDS
                    db = SessionLocal()
                    from src.database.queries import store_predictions
                    
                    pred_data = [
                        (
                            p["date"],
                            p["predicted_rate"],
                            p["confidence_lower"],
                            p["confidence_upper"]
                        )
                        for p in predictions
                    ]
                    
                    store_predictions(db, route, pred_data, "v1")
                    db.close()
                    model_count += 1
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to train model for {route}: {e}")
                continue
        
        logger.info(f"✅ Trained {model_count} ARIMA models")
        
        # 7. Save processed data to S3
        logger.info("💾 Uploading processed data to S3")
        
        try:
            processed_key = f"processed/{datetime.now().strftime('%Y-%m-%d')}/freight_data.csv"
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            
            s3_client.put_object(
                Bucket=bucket,
                Key=processed_key,
                Body=csv_buffer.getvalue()
            )
            logger.info(f"✅ Uploaded processed data to {processed_key}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to upload processed data: {e}")
        
        # Success response
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "ETL pipeline completed successfully",
                "records_processed": len(df),
                "models_trained": model_count,
                "timestamp": datetime.utcnow().isoformat()
            })
        }
    
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
'''

with open(f"{project_root}/lambda_handler.py", "w") as f:
    f.write(lambda_handler)

print("✅ Created Lambda handler")