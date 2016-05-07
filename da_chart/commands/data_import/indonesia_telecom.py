
from collections import OrderedDict

from flask.ext.script import Command as BaseCommand
from flask import current_app as app

from retsku.api.models import db, Customer
from retsku.api.pop_models import (POPTask, POPAdType, POPPromotion,
                                   POPTaskProvider)


class Command(BaseCommand):

    CUSTOMER_NAME = 'Indonesia Telecom'
    TASK_NAME = 'Indonesia Telecom POP Task'
    PROVIDERS = ['Indosat', 'IM3',
                 'Mentari', 'Telkomsel', 'Simpati',
                 'Kartu AS', 'Loop', 'XL', 'AXIS', '3(THREE)', 'Smartfren']
    AD_TYPES = ['Posters', 'Standing Banner', 'Banners', 'Brochure', 'Dangler',
                'Sticker']
    PROMOTIONS = {
        'Indosat': [
            'Internet cepat (3 Gb 90 hari)', 'Jaringan Baru Super 4G-LTE',
            'Program aktivasi MOBO Berhadiah nonton BARCA',
            'Pint@rnet 24 Jam Sebulan',
            'Pint@rnet Gratis 30 Menit Nelpon & SMS setiap hari',
            'Pint@rnet Gratis Internet 1 G Sebulan',
            'Pint@rnet internet.org Internet Tanpa Pulsa Untuk Semua',
            'Ooredoo – 4G plus', 'Ooredoo'],
        'IM3': [
            'Ngobrol', 'Play Nelpon & SMS', 'Play Online',
            'IM3 Gratis Nelpon 30 menit', 'Play Soulmate', 'Play 24 Jam',
            '8 GB Rp 39.000', 'Internet cepat (3 Gb 90 hari)',
            'Pint@rnet 24 Jam Sebulan',
            'Pint@rnet Gratis 30 Menit Nelpon & SMS setiap hari',
            'Pint@rnet Gratis Internet 1 G Sebulan',
            'Pint@rnet internet.org Internet Tanpa Pulsa Untuk Semua',
            'Ketupat (Keuntungan Berlipat: termasuk promo Santan,Telor, Opor dan Komplit)',
            'Ooredoo – 4G plus', 'Ooredoo',
            'Rp 1 per detik nelpon ke semua operator',
            'Bonus 4G 10 GB', 'Ooredoo Freedom combo (Unspecified)',
            'Ooredoo Freedom combo – paket m',
            'Ooredoo Freedom combo – paket l',
            'Ooredoo Freedom combo – paket xl',
            'Ooredoo Freedom combo – paket xxl'],
        'Mentari': [
            'Obrol-obrol', '3 GB 3 Months', 'Internet cepat (3 Gb 90 hari)',
            '3GB+', 'Ooredoo'],
        'Telkomsel': [
            'Siaga', '4G LTE',
            'TSEL penukaran point dengan hadiah Umroh, tiket, mobil, dll',
            'Haji', 'Loop Sharing-an ',
            'Paket TAU (Telkomsel Android United) Mingguan ',
            'Redeem poin program'],
        'Simpati': [
            'Talkmania', 'Gila online/ Online holic',
            'Loop gratis data 1.2GB', 'InternetMania Ultima', 'Social Max'],
        'Kartu AS': [
            'Kartu As Buat Loh (Kasbuloh)', '500 (Gope)',
            'New SP (Makin PAS buat Semua)', 'Gampang Internetan',
            'Kenyang Internetan'],
        'Loop': ['SEMAULOOP'],
        'XL': [
            'Ku', 'Bebas (gratis internetan 6 bulan)',
            'Internet Super Unlimited', 'XtraOn',
            'Paket Internet Chatting & Browsing Setahun',
            '4G LTE (XL New Logo) - Sekarang Bisa', 'Buat Paket sesukamu',
            'HotRod 24 hours', 'HotRod 4G',
            'Program isi ulang pulsa berhadiah 60 Mazda 2', 'HotRod 50',
            'Tabungan Kuota 4G (4G Tank)',
            'Reload program Mazda CX-5 (atau PoinSiul / Poin Isi Ulang)',
            'Beli Paket XL Untung Segudang', 'HotRod 4G (New Visual)',
            'HotRod paket kuota', ],
        'AXIS': [
            'Rejeki Axis', 'Iritology', 'New SP Horee!', 'Rabu Rawit'],
        '3(THREE)': [
            'Always on',  'Indie+ (pakai duluan bayar belakangan)',
            'Cengli (Bonus Goceng Berkali-kali)',
            'Bonus telepon hingga berhari-hari/ Bicara kok bayar',
            'New SP Get More', ],
        'Smartfren': []
    }

    def run(self):
        customer = Customer.query.filter(
                Customer.name == self.CUSTOMER_NAME).first()
        if customer:
            raise Exception('Customer {} already exists'.format(
                            self.CUSTOMER_NAME))

        customer = Customer(name=self.CUSTOMER_NAME)
        task = POPTask(name=self.TASK_NAME)
        task.customer = customer

        providers = OrderedDict()
        for name in self.PROVIDERS:
            providers[name] = POPTaskProvider(name=name)

        task.providers = list(providers.values())

        for name in self.AD_TYPES:
            task.ad_types.append(POPAdType(name=name))

        for provider_name, promotions in self.PROMOTIONS.items():
            provider = providers[provider_name]
            for promotion in promotions:
                task.promotions.append(POPPromotion(name=promotion,
                                                    provider=provider))

        db.session.add(customer)
        db.session.commit()
