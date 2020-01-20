from flask import Flask,render_template,request,render_template_string,session,redirect,url_for,flash,g
from flask_sqlalchemy import SQLAlchemy
from flask_user import current_user, UserManager, UserMixin
#from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
from sqlalchemy.sql import select
from sqlalchemy import create_engine,MetaData, Table, Column,Integer,String,ForeignKey
from sqlalchemy import and_
from datetime import datetime
from functools import wraps
import time
from collections import defaultdict

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='mssql://@DESKTOP-1LS3J6I\MSSQLSERVER01/ucakRezervasyon?driver=SQL Server Native Client 11.0'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False
app.secret_key="Emre Karaca"

db=SQLAlchemy(app)

class tbl_musteri(db.Model,UserMixin):
    __tablename__="tbl_musteri"
    musteriId=db.Column(db.Integer(),primary_key=True)
    musteriAd=db.Column(db.String(25),nullable=False)
    musteriSoyad=db.Column(db.String(25),nullable=False)
    kullaniciAdi=db.Column(db.String(25),nullable=False)
    sifre=db.Column(db.String(25),nullable=False)
    bonus=db.Column(db.Integer(),nullable=True)
    #roles = db.relationship('tbl_role', secondary='tbl_MusteriRol')

class tbl_rol(db.Model,UserMixin):
    __tablename__="tbl_rol"
    rolId=db.Column(db.Integer(),primary_key=True)
    rol=db.Column(db.String())

class tbl_MusteriRol(db.Model,UserMixin):
    __tablename__="tbl_MusteriRol"
    MusteriRolId=db.Column(db.Integer(),primary_key=True)
    musteriId=db.Column(db.Integer(),db.ForeignKey("tbl_musteri.musteriId",ondelete="CASCADE"))
    rolId=db.Column(db.Integer(),db.ForeignKey("tbl_rol.rolId",ondelete="CASCADE"))

class tbl_fiyat(db.Model,UserMixin):
    __tablename__="tbl_fiyat"
    fiyatId=db.Column(db.Integer(),primary_key=True)
    rotaId=db.Column(db.Integer(),db.ForeignKey("tbl_rota.rotaId",ondelete="CASCADE"))
    sirketUcakId=db.Column(db.Integer(),db.ForeignKey("tbl_sirketUcak.sirketUcakId",ondelete="CASCADE"))
    fiyat=db.Column(db.Integer())

class tbl_rezervasyon(db.Model,UserMixin):
    __tablename__="tbl_rezervasyon"
    rezervasyonId=db.Column(db.Integer(),primary_key=True)
    ucusId=db.Column(db.Integer(),db.ForeignKey("tbl_ucus.ucusId",ondelete="CASCADE"))
    musteriId=db.Column(db.Integer(),db.ForeignKey("tbl_musteri.musteriId",ondelete="CASCADE"))
    rezervasyonTarih=db.Column(db.DateTime())
    odemeYapildiMi=db.Column(db.Boolean())
    rBiletSahibiAd=db.Column(db.String(25))
    rBiletSahibiSoyad=db.Column(db.String(25))
    rBiletSahibiTC=db.Column(db.String(11))

class tbl_rota(db.Model,UserMixin):
    __tablename__="tbl_rota"
    rotaId=db.Column(db.Integer(),primary_key=True)
    kalkisSehirId=db.Column(db.Integer(),db.ForeignKey("tbl_sehir.sehirId",ondelete="CASCADE"))
    varisSehirId=db.Column(db.Integer(),db.ForeignKey("tbl_sehir.sehirId",ondelete="CASCADE"))

class tbl_sehir(db.Model,UserMixin):
    __tablename__="tbl_sehir"
    sehirId=db.Column(db.Integer(),primary_key=True)
    sehirAd=db.Column(db.String(25))
    ulkeId=db.Column(db.Integer(),db.ForeignKey("tbl_ulke.ulkeId",ondelete="CASCADE"))
    sehirSilindiMi=db.Column(db.Boolean())

class tbl_sirket(db.Model,UserMixin):
    __tablename__="tbl_sirket"
    sirketId=db.Column(db.Integer(),primary_key=True)
    sirketAd=db.Column(db.String(50))
    sirketSilindiMi=db.Column(db.Boolean())

class tbl_sirketUcak(db.Model,UserMixin):
    __tablename__="tbl_sirketUcak"
    sirketUcakId=db.Column(db.Integer(),primary_key=True)
    sirketId=db.Column(db.Integer(),ForeignKey("tbl_sirket.sirketId",ondelete="CASCADE"))
    ucakId=db.Column(db.Integer(),ForeignKey("tbl_ucak.ucakId",ondelete="CASCADE"))
    sirketUcakSilindiMi=db.Column(db.Boolean())

class tbl_ucak(db.Model,UserMixin):
    __tablename__="tbl_ucak"
    ucakId=db.Column(db.Integer(),primary_key=True)
    ucakModel=db.Column(db.String())
    ucakKoltukSayisi=db.Column(db.Integer())
    ucakSilindiMi=db.Column(db.Boolean())

class tbl_ucus(db.Model,UserMixin):
    __tablename__="tbl_ucus"
    ucusId=db.Column(db.Integer(),primary_key=True)
    fiyatId=db.Column(db.Integer(),ForeignKey("tbl_fiyat.fiyatId",ondelete="CASCADE"))
    ucusTarih=db.Column(db.DateTime())
    ucusSaat=db.Column(db.String(10))

class tbl_ulke(db.Model,UserMixin):
    __tablename__="tbl_ulke"
    ulkeId=db.Column(db.Integer(),primary_key=True)
    ulkeAd=db.Column(db.String(25))
    ulkeSilindiMi=db.Column(db.Boolean())

#user_manager = UserManager(app, db, tbl_musteri)
db.metadata.clear()
db.create_all()

class Sepet:
    i=0
    urunler={}



#Giriş yapılmış mı? bunu kontrol eder.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "girisYapildiMi" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapmalısınız...","danger")
            return redirect(url_for("uye_giris"))
    return decorated_function

def roles_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "girisYapildiMi" in session:
            if tbl_MusteriRol.query.filter(tbl_MusteriRol.musteriId==session["kullaniciId"]).first():
                gelenVeri=tbl_MusteriRol.query.filter(tbl_MusteriRol.musteriId==session["kullaniciId"]).first()
                gelenVeri2=tbl_rol.query.filter(tbl_rol.rol=="Admin").first()
                if gelenVeri.rolId==gelenVeri2.rolId:
                    return f(*args, **kwargs)
                else:
                    flash("Bu sayfayı görüntülemek için Admin yetkinizin olması gerek...","danger")
                    return redirect(url_for("anasayfa"))
            else:
                flash("Bu sayfayı görüntüleme yetkiniz yok...","danger")
                return redirect(url_for("anasayfa"))
        else:
            flash("Bu sayfayı görüntülemek için Admin yetkinizin olması gerekir...","danger")
            return redirect(url_for("uye_giris"))
    return decorated_function

@app.route("/",methods=["GET","POST"])
def anasayfa():
    
    if request.method=="GET":
        
        dictUcuslar=dict()
        ucuslar = db.session.query(tbl_ucus).all()
        for ucus in ucuslar:
        
            s = db.session.query(tbl_fiyat.fiyat).filter(tbl_fiyat.fiyatId==ucus.fiyatId)
            for row in s:
                ucusFiyati=str(row)[10:-4]

                ucusTarihi=ucus.ucusTarih

                ucusSaati=ucus.ucusSaat

            s=db.session.query(tbl_sehir.sehirAd).filter(tbl_sehir.sehirId==tbl_rota.kalkisSehirId).filter(tbl_rota.rotaId==tbl_fiyat.rotaId).filter(tbl_ucus.fiyatId==ucus.fiyatId)
            for row in s:
                kalkisSehri=str(row)[2:-3]

            s=db.session.query(tbl_sehir.sehirAd).filter(tbl_sehir.sehirId==tbl_rota.varisSehirId).filter(tbl_rota.rotaId==tbl_fiyat.rotaId).filter(tbl_ucus.fiyatId==ucus.fiyatId)
            for row in s:
                varisSehri=str(row)[2:-3]

            s=db.session.query(tbl_sirket.sirketAd).filter(tbl_sirket.sirketId==tbl_sirketUcak.sirketId).filter(tbl_sirketUcak.sirketUcakId==tbl_fiyat.sirketUcakId).filter(tbl_fiyat.fiyatId==ucus.fiyatId)
            for row in s:
                ucusSirketAdi= str(row)[2:-3]

            s=db.session.query(tbl_ucak.ucakModel).filter(tbl_ucak.ucakId==tbl_sirketUcak.ucakId).filter(tbl_sirketUcak.sirketUcakId==tbl_fiyat.sirketUcakId).filter(tbl_fiyat.fiyatId==ucus.fiyatId)
            for row in s:
                ucusUcakModeli = str(row)[2:-3]

            dictUcuslar[ucus.ucusId]={"kalkisSehri":kalkisSehri,"varisSehri":varisSehri,"ucusSirketAdi":ucusSirketAdi,"ucusUcakModeli":ucusUcakModeli,"ucusFiyati":ucusFiyati,"ucusTarihi":ucusTarihi,"ucusSaati":ucusSaati}

    
        return render_template("anasayfa.html",ucuslar=dictUcuslar)

@app.route("/uye_ol",methods=["GET","POST"])
def uye_ol():
    if request.method=="POST":
        try:
            isim=request.form["musteriAd"]
            soyisim=request.form["musteriSoyad"]
            kullaniciAdi=request.form["kullaniciAdi"]
            sifre=request.form["sifre"]
            musteri=tbl_musteri(
                musteriAd=isim,
                musteriSoyad=soyisim,
                kullaniciAdi=kullaniciAdi,
                sifre=sifre
            )
            
            db.session.add(musteri)
            db.session.commit()
            
            flash("Kayıt İşleminiz Gerçekleştirildi...","success")
            
            return redirect(url_for("uye_giris"))

        except:
            flash("Kayıt İşleminiz Gerçekleştirilemedi...","danger")
            return render_template("uye_ol.html")
    else:
        return render_template("uye_ol.html")

@app.route("/uye_giris",methods=["GET","POST"])
def uye_giris():
    if request.method == "POST":
        girilenKullaniciAdi=request.form["kullaniciAdi"]
        girilenSifre=request.form["sifre"]
        
        if tbl_musteri.query.filter(tbl_musteri.kullaniciAdi==girilenKullaniciAdi).first():
            gelenVeri = tbl_musteri.query.filter(tbl_musteri.kullaniciAdi==girilenKullaniciAdi).first()
            if girilenSifre==gelenVeri.sifre:
                flash("Giriş işlemi başarılı...","success")
                session["girisYapildiMi"]=True
                session["kullaniciAdi"]=gelenVeri.kullaniciAdi
                session["kullaniciId"]=gelenVeri.musteriId
                global sepet
                sepet=Sepet()
                return redirect(url_for("anasayfa"))
            else:
                flash("Girdiğiniz şifre yanlış","danger")
                return render_template("uye_giris.html")
        
        else:
            flash("Böyle bir kullanıcı yok","danger")
            return redirect(url_for("uye_giris"))
    
    else:
        return render_template("uye_giris.html")

@app.route("/uye_cikis")
def cikisYap():
    session.clear()
    global sepet
    del sepet
    return redirect(url_for("anasayfa"))

@app.route("/admin")
@roles_required
def admin():
    return render_template("admin.html")

@app.route("/sirket_ekle",methods=["GET","POST"])
@roles_required
def sirket_ekle():
    if request.method=="POST":
        try:
            girilenSirketAdi=request.form["sirketAdi"]
            varMi=tbl_sirket.query.filter_by(sirketAd=girilenSirketAdi).first()
            if varMi:
                if varMi.sirketSilindiMi:
                    varMi.sirketSilindiMi=False
                    db.session.commit()
                    flash("Şirket ekleme başarılı...","success")
                    return redirect(url_for("admin"))
                else:
                    flash("Böyle bir şirket zaten var...","danger")
                    return redirect(url_for("sirket_ekle"))

            else:
                sirket = tbl_sirket(
                    sirketAd=girilenSirketAdi,
                    sirketSilindiMi=False
                )

                db.session.add(sirket)
                db.session.commit()

                flash("Şirket ekleme başarılı...","success")
                return redirect(url_for("admin"))
        except Exception as hata:
            flash("Ekleme sırasında hata oluştu..."+"Hata: " +str(hata),"danger")
            return redirect(url_for("sirket_ekle"))
    else:
        return render_template("sirket_ekle.html")

@app.route("/sirket_sil",methods=["GET","POST"])
@roles_required
def sirket_sil():
    if request.method=="GET":
        sirketler=db.session.query(tbl_sirket).filter_by(sirketSilindiMi=False).all()
        return render_template("sirket_sil.html",sirketler=sirketler)
    else:
        secilenSirket=request.form["sirket"]
        sirket=tbl_sirket.query.filter_by(sirketId=secilenSirket).first()
        sirket.sirketSilindiMi=True
        db.session.commit()
        flash("Sirket silme işlemi başarılı...","success")
        return redirect(url_for("admin"))

@app.route("/sirket_duzenle",methods=["GET","POST"])
@roles_required
def sirket_duzenle():
    if request.method=="GET":
        sirketler=db.session.query(tbl_sirket).filter_by(sirketSilindiMi=False).all()
        return render_template("sirket_duzenle.html",sirketler=sirketler)
    else:
        secilenSirket=request.form["sirket"]
        girilenSirketAdi=request.form["sirketAd"]

        sirket=tbl_sirket.query.filter_by(sirketId=secilenSirket).first()
        sirket.sirketAd=girilenSirketAdi

        db.session.commit()

        flash("Şirket güncelleme işlemi başarılı...","success")
        return redirect(url_for("admin"))


@app.route("/ucak_ekle",methods=["GET","POST"])
@roles_required
def ucak_ekle():
    if request.method=="POST":
        try:
            girilenUcakModeli=request.form["ucakModeli"]
            girilenKoltukSayisi=request.form["ucakKoltukSayisi"]
            secilenSirket=int(request.form["sirket"])
            
            ucakVarMi = tbl_ucak.query.filter_by(ucakModel=girilenUcakModeli).first()
            
            if ucakVarMi:
                if ucakVarMi.ucakSilindiMi:
                    ucakVarMi.ucakSilindiMi=False
                    db.session.commit()
                    flash("Uçak ekleme işlemi başarılı...","success")
                    return redirect(url_for("admin"))
                else:
                    flash("Böyle bir uçak zaten var...","success")
                    return redirect(url_for("admin"))
                    
            
            else:
                ucak = tbl_ucak(
                ucakModel=girilenUcakModeli,
                ucakKoltukSayisi=girilenKoltukSayisi,
                ucakSilindiMi=False
                )

                db.session.add(ucak)
                db.session.commit()

                sorgu=tbl_ucak.query.filter(tbl_ucak.ucakModel==girilenUcakModeli).first()
                eklenenUcakId=sorgu.ucakId

                sirketUcak = tbl_sirketUcak(
                sirketId=secilenSirket,
                ucakId=eklenenUcakId,
                sirketUcakSilindiMi=False
                )

                db.session.add(sirketUcak)
                db.session.commit()

                flash("Uçak ekleme başarılı...","success")
                return redirect(url_for("admin"))
        except Exception as hata:
            flash("Ekleme sırasında hata oluştu..." + " Hata: "+str(hata),"danger")
            return redirect(url_for("ucak_ekle"))
    else:
        sirketler=db.session.query(tbl_sirket).filter_by(sirketSilindiMi=False).all()
        return render_template("ucak_ekle.html",sirketler=sirketler)

@app.route("/ucak_sil",methods=["GET","POST"])
@roles_required
def ucak_sil():
    if request.method=="GET":
        ucaklar=tbl_ucak.query.filter_by(ucakSilindiMi=False).all()
        flash("DİKKAT! SİLECEĞİNİZ UÇAK AİT OLDUĞU ŞİRKETTEN DE SİLİNECEKTİR...","danger")
        return render_template("ucak_sil.html",ucaklar=ucaklar)
    else:
        secilenUcak=request.form["ucak"]
        ucak=tbl_ucak.query.filter_by(ucakId=secilenUcak).first()
        ucak.ucakSilindiMi=True

        sirketUcaklar = tbl_sirketUcak.query.filter_by(ucakId=secilenUcak).all()

        for sU in sirketUcaklar:
            sU.sirketUcakSilindiMi=True
            db.session.commit()

        flash("Uçak silme işlemi başarılı...","success")
        return redirect(url_for("admin"))

@app.route("/ucak_guncelle",methods=["GET","POST"])
@roles_required
def ucak_guncelle():
    if request.method=="GET":
        ucaklar = db.session.query(tbl_ucak).filter_by(ucakSilindiMi=False).all()
        sirketler=db.session.query(tbl_sirket).filter_by(sirketSilindiMi=False).all()
        return render_template("ucak_guncelle.html",ucaklar=ucaklar,sirketler=sirketler)

    else:
        try:
            girilenUcakModeli=request.form["ucakModeli"]
            girilenKoltukSayisi=int(request.form["koltukSayisi"])
            secilenSirket=request.form["sirket"]
            degistirilecekUcak=request.form["ucak"]

            ucakVarMi = db.session.query(tbl_ucak).filter(tbl_ucak.ucakModel==girilenUcakModeli).filter(tbl_ucak.ucakId!=degistirilecekUcak).first()
            if ucakVarMi:
                flash("Girdiğiniz model de bir uçak zaten var...","danger")
                return redirect(url_for("ucak_guncelle"))
            else:
                ucak=db.session.query(tbl_ucak).filter_by(ucakId=degistirilecekUcak).first()

                ucak.ucakModel=girilenUcakModeli
                ucak.ucakKoltukSayisi=girilenKoltukSayisi
                ucak.ucakSilindiMi=False

                db.session.commit()

                flash("Uçak güncelleme işlemi başarılı...","success")
                return redirect(url_for("admin"))
            #flash(str(ucakVarMi))
            #return redirect(url_for("admin"))

            # ucakVarMi = tbl_ucak.query.filter_by(ucakModel=girilenUcakModeli).first()
            # if ucakVarMi.ucakId==degistirilecekUcak and ucakVarMi!=None and ucakVarMi.ucakSilindiMi!=False:
            #     flash("Girdiğiniz model de bir uçak zaten var...","danger")
            #     return redirect(url_for("ucak_guncelle"))
            # else:
            #     ucak = tbl_ucak.query.filter_by(ucakId=degistirilecekUcak).first()

            #     ucak.ucakModel=girilenUcakModeli
            #     ucak.koltukSayisi=girilenKoltukSayisi
            #     ucak.ucakSilindiMi=False

            #     db.session.commit()

            #     sirketUcak = tbl_sirketUcak(
            #         sirketId=secilenSirket,
            #         ucakId=degistirilecekUcak,
            #         sirketUcakSilindiMi=False
            #     )

            #     db.session.add(sirketUcak)
            #     db.session.commit()

            #     flash("Uçak güncelleme başarılı...","success")
            #     return redirect(url_for("admin"))
        except Exception as hata:
            flash("Güncelleme sırasında hata oluştu..." + " Hata : "+str(hata),"danger")
            return redirect(url_for("admin"))

@app.route("/ulke_sil",methods=["GET","POST"])
@roles_required
def ulke_sil():
    if request.method=="GET":
        ulkeler=db.session.query(tbl_ulke).filter(tbl_ulke.ulkeSilindiMi==False).all()
        flash("DİKKAT! BİR ÜLKEYİ SİLERSENİZ O ÜLKEDEKİ ŞEHİRLERDE SİLİNECEKTİR...","danger")
        return render_template("ulke_sil.html",ulkeler=ulkeler)

    else:
        silinecekUlke=request.form["ulke"]

        ulke=db.session.query(tbl_ulke).filter_by(ulkeId=silinecekUlke).first()
        ulke.ulkeSilindiMi=True

        db.session.commit()

        sehirler = db.session.query(tbl_sehir).filter_by(ulkeId=silinecekUlke).all()

        for sehir in sehirler:
            sehir.sehirSilindiMi=True

        db.session.commit()

        

        flash("Ülke silme işlemi başarılı...","success")
        return redirect(url_for("admin"))


@app.route("/ulke_guncelle",methods=["GET","POST"])
@roles_required
def ulke_guncelle():
    if request.method=="GET":
        ulkeler=db.session.query(tbl_ulke).filter_by(ulkeSilindiMi=False).all()
        return render_template("ulke_guncelle.html",ulkeler=ulkeler)
    else:
        guncellenecekUlke=request.form["ulke"]
        girilenUlkeAdi=request.form["ulkeAdi"]

        ulke=tbl_ulke.query.filter_by(ulkeId=guncellenecekUlke).first()
        ulke.ulkeAd=girilenUlkeAdi

        db.session.commit()

        flash("Ülke güncelleme işlemi başarılı...","success")
        return redirect(url_for("admin"))


@app.route("/ulke_ekle",methods=["GET","POST"])
@roles_required
def ulke_ekle():
    if request.method=="POST":
        try:
            girilenUlkeAdi=request.form["ulkeAd"]
            
            ulkeVarMi=db.session.query(tbl_ulke).filter_by(ulkeAd=girilenUlkeAdi).fisrt()
            if ulkeVarMi:
                flash("Bu ülke zaten var...","danger")
                return redirect(url_for("ulke_ekle"))
            else:
                ulke = tbl_ulke(
                    ulkeAd=girilenUlkeAdi
                )

                db.session.add(ulke)
                db.session.commit()

                flash("Ülke ekleme başarılı...","success")
                return redirect(url_for("admin"))
        except:
            flash("Ekleme sırasında hata oluştu...","danger")
            return redirect(url_for("ulke_ekle"))
    else:
        return render_template("ulke_ekle.html")

@app.route("/sehir_ekle",methods=["GET","POST"])
@roles_required
def sehir_ekle():
    if request.method=="POST":
        try:
            girilenSehir=request.form["sehir"]

            sehirVarMi=db.session.query(tbl_sehir).filter_by(sehirAd=girilenSehir).first()
            
            if sehirVarMi:
                flash("Bu şehir zaten var...","danger")
                return redirect(url_for("sehir_ekle"))
            else:
                secilenUlke=int(request.form["ulke"])
                sehir = tbl_sehir(
                    sehirAd=girilenSehir,
                    ulkeId=secilenUlke
                )

                db.session.add(sehir)
                db.session.commit()

            

                flash("Şehir ekleme başarılı...","success")
                return redirect(url_for("admin"))
        except:
            flash("Ekleme sırasında hata oluştu...","danger")
            return redirect(url_for("sehir_ekle"))
    else:
        ulkeler=db.session.query(tbl_ulke).all()
        return render_template("sehir_ekle.html",ulkeler=ulkeler)

@app.route("/sehir_sil",methods=["GET","POST"])
@roles_required
def sehir_sil():
    if request.method=="GET":
        sehirler = db.session.query(tbl_sehir).filter_by(sehirSilindiMi=False).all()
        return render_template("sehir_sil.html",sehirler=sehirler)
    else:
        silinecekSehir = request.form["sehir"]
        
        sehir=db.session.query(tbl_sehir).filter_by(sehirId=silinecekSehir).first()
        sehir.sehirSilindiMi=True
        db.session.commit()

        flash("Şehir silme işlemi başarılı...","success")
        return redirect(url_for("admin"))


@app.route("/sehir_guncelle",methods=["GET","POST"])
@roles_required
def sehir_guncelle():
    if request.method=="GET":
        ulkeler=db.session.query(tbl_ulke).filter_by(ulkeSilindiMi=False)
        sehirler=db.session.query(tbl_sehir).filter_by(sehirSilindiMi=False)
        return render_template("sehir_guncelle.html",sehirler=sehirler,ulkeler=ulkeler)
    
    else:
        secilenUlke=request.form["ulke"]
        girilenSehirAdi=request.form["sehirAdi"]
        degistirilecekSehir=request.form["sehir"]

        sehirVarMi = tbl_sehir.session.query.filter(tbl_sehir.sehirAd==girilenSehirAdi).filter(tbl_sehir.ulkeId==secilenUlke).first()
        
        if sehirVarMi:
            flash("Bu ülkede bu şehir zaten var...","danger")
            return redirect(url_for("sehir_guncelle"))
        else:
            sehir = db.session.query(tbl_sehir).filter_by(sehirId=degistirilecekSehir)
            sehir.sehirAd=girilenSehirAdi
            sehir.ulkeId=secilenUlke
            db.session.commit()

            flash("Şehir güncelleme işlemi başarılı...","success")
            return redirect(url_for("admin"))

@app.route("/rota_ekle",methods=["GET","POST"])
@roles_required
def rota_ekle():
    if request.method=="POST":
        try:
            secilenKalkisSehri=int(request.form["kalkisSehri"])
            secilenVarisSehri=int(request.form["varisSehri"])
            
            rota = tbl_rota(
                kalkisSehirId=secilenKalkisSehri,
                varisSehirId=secilenVarisSehri
            )

            db.session.add(rota)
            db.session.commit()

            

            flash("Rota ekleme başarılı...","success")
            return redirect(url_for("admin"))
        except:
            flash("Ekleme sırasında hata oluştu...","danger")
            return redirect(url_for("rota_ekle"))
    else:
        sehirler=db.session.query(tbl_sehir).all()
        return render_template("rota_ekle.html",sehirler=sehirler)

@app.route("/fiyat_ekle",methods=["GET","POST"])
@roles_required
def fiyat_ekle():
    if request.method=="POST":
        try:
            secilenRota = request.form["rota"]
            secilenSirketUcak=request.form["sirketUcak"]
            girilenFiyat=request.form["fiyat"]
            
            fiyat=tbl_fiyat(
                rotaId=secilenRota,
                sirketUcakId=secilenSirketUcak,
                fiyat=girilenFiyat
            )

            db.session.add(fiyat)
            db.session.commit()

            

            flash("Fiyat ekleme başarılı...","success")
            return redirect(url_for("admin"))
        except:
            flash("Ekleme sırasında hata oluştu...","danger")
            return redirect(url_for("fiyat_ekle"))
    else:
        diziRotalar=dict()
        rotalar=db.session.query(tbl_rota).all()
        for rota in rotalar:
            s = select([tbl_sehir.sehirAd]).where(tbl_sehir.sehirId == rota.kalkisSehirId)
            for row in db.session.execute(s):
                kalkisSehri=str(row)[2:-3]
    
            s=select([tbl_sehir.sehirAd]).where(tbl_sehir.sehirId == rota.varisSehirId)
            for row in db.session.execute(s):
                varisSehri=str(row)[2:-3]
            
            diziRotalar[rota.rotaId]={"kalkisSehri":kalkisSehri,"varisSehri":varisSehri}

        dictSirketUcak=dict()
        sirketUcak=db.session.query(tbl_sirketUcak).all()

        for sU in sirketUcak:
            s=select([tbl_sirket.sirketAd]).where(tbl_sirket.sirketId == sU.sirketId)
            for row in db.session.execute(s):
                sirketAd=str(row)[2:-3]

            s=select([tbl_ucak.ucakModel]).where(tbl_sirketUcak.ucakId==sU.ucakId)
            for row in db.session.execute(s):
                ucakModel=str(row)[2:-3]
            
            dictSirketUcak[sU.sirketUcakId]={"sirket":sirketAd,"ucakModel":ucakModel}
        
        return render_template("fiyat_ekle.html",rotalar=diziRotalar,sirketUcak=dictSirketUcak)

@app.route("/ucus_ekle",methods=["GET","POST"])
@roles_required
def ucus_ekle():
    if request.method=="POST":
        try:
            secilenUcus=request.form["ucus"]
            ucusTarihi=request.form["ucusTarihi"]
            ucusSaati=request.form["ucusSaati"]

            ucus=tbl_ucus(
                fiyatId=secilenUcus,
                ucusTarih=ucusTarihi,
                ucusSaat=ucusSaati
            )

            db.session.add(ucus)
            db.session.commit()

            flash("Uçuş ekleme başarılı...","success")
            return redirect(url_for("admin"))
        
        except:
            flash("Ekleme sırasında hata oluştu...","danger")
            return redirect(url_for("ucus_ekle"))
    else:
        dictUcus=dict()
        fiyatlar = db.session.query(tbl_fiyat).all()
        
        for fiyat in fiyatlar:
            s=db.session.query(tbl_sehir.sehirAd).filter(tbl_rota.kalkisSehirId==tbl_sehir.sehirId).filter(tbl_rota.rotaId==tbl_fiyat.rotaId).filter(tbl_fiyat.fiyatId==fiyat.fiyatId)
            for row in s:
                kalkisSehri=str(row)[2:-3]
            
            s=db.session.query(tbl_sehir.sehirAd).filter(tbl_rota.varisSehirId==tbl_sehir.sehirId).filter(tbl_rota.rotaId==tbl_fiyat.rotaId).filter(tbl_fiyat.fiyatId==fiyat.fiyatId)
            for row in s:
                varisSehri=str(row)[2:-3]
            
            s=db.session.query(tbl_sirket.sirketAd).filter(tbl_sirket.sirketId==tbl_sirketUcak.sirketId).filter(tbl_sirketUcak.sirketUcakId==fiyat.sirketUcakId)
            for row in s:
                ucusSirketi=str(row)[2:-3]

            s=db.session.query(tbl_ucak.ucakModel).filter(tbl_ucak.ucakId==tbl_sirketUcak.ucakId).filter(tbl_sirketUcak.sirketUcakId==fiyat.sirketUcakId)
            for row in s:
                ucusUcakModeli=str(row)[2:-3]

            ucusFiyati=fiyat.fiyat

            dictUcus[fiyat.fiyatId]={"kalkisSehri":kalkisSehri,"varisSehri":varisSehri,"ucusSirketi":ucusSirketi,"ucusUcakModeli":ucusUcakModeli,"ucusFiyati":ucusFiyati}


            
        
        return render_template("ucus_ekle.html",fiyatlar=dictUcus)        

@app.route("/rezervasyon_yap",methods=["GET","POST"])
@login_required
def rezervasyon_yap():
    
    if request.method == "GET":
        global secilenUcusId
        secilenUcusId=request.args.get('ucus_id')
        return render_template("rezervasyon_yap.html",ucusId=secilenUcusId)
    else:
        global ucusId
        ucusId=secilenUcusId
        global sepet
        biletSahibiAdi=request.form["biletSahibiAd"]
        biletSahibiSoyadi=request.form["biletSahibiSoyad"]
        biletSahiciTC=request.form["biletSahibiTC"]
        #simdi=time.strftime(r"%d.%m.%Y %H:%M:%S", time.localtime())
        #simdi=str(time.strftime(r"%Y.%m.%d %H:%M:%S", time.localtime()))
        simdi=datetime.now()    
        sepet.urunler[sepet.i]={"ucusId":ucusId,"rezervasyonSaati":simdi,"biletSahibiAd":biletSahibiAdi,"biletSahibiSoyad":biletSahibiSoyadi,"biletSahibiTC":biletSahiciTC}
        sepet.i=sepet.i+1
        flash("ürünler sepete eklendi...","success")
        return redirect(url_for("anasayfa"))
        

        # rezervasyon=tbl_rezervasyon(
        #     ucusId=secilenUcusId,
        #     musteriId=session["kullaniciId"],
        #     rezervasyonTarih=datetime.now,
        #     odemeYapildiMi=False,
        #     rBiletSahibiAd=biletSahibiAdi,
        #     rBiletSahibiSoyad=biletSahibiSoyadi,
        #     rBiletSahibiTC=biletSahiciTC
        # )

        # db.session.add(rezervasyon)
        # db.session.commit()

@app.route("/rezervasyon_guncelle",methods=["GET","POST"])
@login_required
def rezervasyon_guncelle():
    global secilenRezervasyon
    if request.method=="GET":
        global secilenRezervasyon
        secilenRezervasyon=request.args.get('sepetKey')
        secilenRezervasyon=int(secilenRezervasyon)
        return render_template("rezervasyon_guncelle.html")
    else:
        global sepet
        
        biletSahibiAdi=request.form["biletSahibiAd"]
        biletSahibiSoyadi=request.form["biletSahibiSoyad"]
        biletSahiciTC=request.form["biletSahibiTC"]
        
        sepet.urunler[secilenRezervasyon]["biletSahibiTC"]=biletSahiciTC
        sepet.urunler[secilenRezervasyon]["biletSahibiSoyad"]=biletSahibiSoyadi
        sepet.urunler[secilenRezervasyon]["biletSahibiAd"]=biletSahibiAdi

        flash("Güncelleme başarılı...","success")
        return redirect(url_for("sepet"))
        
    



@app.route("/sepet",methods=["GET","POST"])
@login_required
def sepet():
    if request.method=="GET":
        global sepet
        simdi=datetime.now()
        for urun in list(sepet.urunler.keys()):
            rezervasyonSaati=sepet.urunler[urun]["rezervasyonSaati"]
            sonuc=simdi-rezervasyonSaati
            if (sonuc.seconds)/60 >1:  
                del sepet.urunler[urun] 
        return render_template("sepet.html",spt=sepet.urunler)

@app.route("/odeme_yap",methods=["POST","GET"])
@login_required
def odeme_yap():
    global secilenRezervasyon
    if request.method=="GET":
        global sepet

        global secilenRezervasyon
        secilenRezervasyon=request.args.get('sepetKey')
        secilenRezervasyon=int(secilenRezervasyon)

        
        s = db.session.query(tbl_fiyat.fiyat).filter(tbl_fiyat.fiyatId==tbl_ucus.fiyatId).filter(tbl_ucus.ucusId==sepet.urunler[secilenRezervasyon]["ucusId"])
        for row in s:
            tutar=str(row)[10:-4]
        
        s=db.session.query(tbl_musteri.bonus).filter(tbl_musteri.musteriId==session["kullaniciId"])
        for row in s:
            bonus=str(row)[1:-2]
        
        return render_template("odeme_yap.html",tutar=tutar,bonus=bonus)

    else:
        bonus=request.form["kullanilanBonus"]
        tutar=request.form["tutar"]
        sonuc=float(tutar)-float(bonus)
        kazanılanBonus = (float(sonuc)*3)/100

        simdi=time.strftime(r"%d.%m.%Y %H:%M:%S", time.localtime())

        rezervasyon = tbl_rezervasyon(
            ucusId=sepet.urunler[secilenRezervasyon]["ucusId"],
            musteriId=session["kullaniciId"],
            rezervasyonTarih=sepet.urunler[secilenRezervasyon]["rezervasyonSaati"],
            odemeYapildiMi=True,
            rBiletSahibiAd=sepet.urunler[secilenRezervasyon]["biletSahibiAd"],
            rBiletSahibiSoyad=sepet.urunler[secilenRezervasyon]["biletSahibiSoyad"],
            rBiletSahibiTC=sepet.urunler[secilenRezervasyon]["biletSahibiTC"]
            )
        db.session.add(rezervasyon)
        db.session.commit()

        musteri = tbl_musteri.query.filter_by(musteriId=session["kullaniciId"]).first()
        musteri.bonus=float(musteri.bonus)+float(kazanılanBonus)-float(bonus)
        db.session.commit()

        del sepet.urunler[secilenRezervasyon]

        flash("Rezervasyonunuz gerçekleştirildi. Ödediğiniz tutar: " + str(sonuc) + "Türk Lirası","success")
        return redirect(url_for("anasayfa"))

    
@app.route("/odeme_yap2",methods=["GET"])
@login_required
def odeme_yap2():
    global sepet
    
    secilenRezervasyon2=request.args.get('sepetKey')
    secilenRezervasyon2=int(secilenRezervasyon2)
    
    simdi=time.strftime(r"%d.%m.%Y %H:%M:%S", time.localtime())

    rezervasyon = tbl_rezervasyon(
        ucusId=sepet.urunler[secilenRezervasyon2]["ucusId"],
        musteriId=session["kullaniciId"],
        rezervasyonTarih=sepet.urunler[secilenRezervasyon2]["rezervasyonSaati"],
        odemeYapildiMi=True,
        rBiletSahibiAd=sepet.urunler[secilenRezervasyon2]["biletSahibiAd"],
        rBiletSahibiSoyad=sepet.urunler[secilenRezervasyon2]["biletSahibiSoyad"],
        rBiletSahibiTC=sepet.urunler[secilenRezervasyon2]["biletSahibiTC"]
        )
    db.session.add(rezervasyon)
    db.session.commit()

    del sepet.urunler[secilenRezervasyon2]
        
    flash("ödeme başarıyla yapıldı...","success")
    return redirect(url_for("anasayfa"))

@app.route("/rezervasyonlarım",methods=["GET"])
@login_required
def rezervasyonlarım():
    rezervasyonlar = db.session.query(tbl_rezervasyon).filter(tbl_rezervasyon.musteriId==session["kullaniciId"])
    return render_template("rezervasyonlarım.html",rezervasyonlarım=rezervasyonlar) 

@app.route("/rezervasyon_sil",methods=["GET"])
@login_required
def rezervasyon_sil():
    global secilenRezervasyon
    secilenRezervasyon=request.args.get("sepetKey")
    secilenRezervasyon=int(secilenRezervasyon)
    global sepet
    del sepet.urunler[secilenRezervasyon]

    flash("Silme işlemi başarılı...","success")
    return redirect(url_for("sepet"))


if __name__ == '__main__':
   app.run(debug = True)