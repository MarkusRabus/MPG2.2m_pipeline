import time
from astropy.io import fits as pf
import glob
import subprocess
import os
import sys
import django
from django.core.exceptions import ObjectDoesNotExist
#from ferospipe import ferospipe


nightfmt="%Y-%m-%d"
copy2root = os.environ['FEROS_DATA_PATH']
sys.path.append(os.environ['DJANGO_PROJECT_PATH'])
from django.apps import apps
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MPG2p2m.settings")
django.setup()

from FEROS.models import *


normal_obsmode = {  'HIERARCH ESO DET READ CLOCK'   : 'R 225Kps Low Gain',
                    'CDELT1'                        : 1,
                    'CDELT2'                        : 1, }


while True:

    current_session = get_session().strftime(nightfmt)
    src_path        = os.environ['DIRECTORY_TO_WATCH'] + current_session
    copy_path       = os.environ['FEROS_DATA_PATH']+current_session+'/RAW/'

    if not os.path.exists(copy_path):
        os.makedirs(copy_path)

    allimages = glob.glob(src_path+'/FEROS*.fits')

    for image in allimages:

        hdr = pf.getheader(image)
        imagename = image.split('/')[-1]

        if normal_obsmode['HIERARCH ESO DET READ CLOCK'] == hdr['HIERARCH ESO DET READ CLOCK'] and \
            normal_obsmode['CDELT1'] == hdr['CDELT1'] and \
            normal_obsmode['CDELT2'] == hdr['CDELT2'] and \
            hdr['HIERARCH ESO TPL NAME'] in HIERARCH_ESO_TPL_NAME:

            cmd='rsync -avz %s %s' %(  image, copy_path+imagename )
            status = subprocess.call(cmd, shell=True)

            print '---------------------------------------------------------------'
            print 'Copy file are:'
            print image
            print copy_path+image.split('/')[-1]
            print '---------------------------------------------------------------'


            try:
                night  = NIGHT.objects.get( calibration_night=current_session )
            except ObjectDoesNotExist:
                night =  NIGHT(calibration_night=current_session ,all_rawcal = False, masterbias = False, masterflat = False, wavesol_flag = False)
                night.save()

            try:
                raw_im  = RAW_IMAGE.objects.get( imagename=imagename )
            except ObjectDoesNotExist:

                if hdr['HIERARCH ESO TPL NAME'] == HIERARCH_ESO_TPL_NAME['bias']:
                    rawobj = RAW_BIAS.objects.create_raw(imagename)
                    rawob.save()
                elif hdr['HIERARCH ESO TPL NAME'] == HIERARCH_ESO_TPL_NAME['flat']:
                    rawobj = RAW_FLAT.objects.create_raw(imagename)
                    rawobj.save()
                elif hdr['HIERARCH ESO TPL NAME'] == HIERARCH_ESO_TPL_NAME['lamp']:
                    rawobj = RAW_LAMP.objects.create_raw(imagename)
                    rawobj.save()
                else:
                    rawobj = RAW_IMAGE.objects.create_raw(imagename)
                    rawobj.save()


            # check if all calibrations 
            bias_list       = RAW_BIAS.objects.filter( session=current_session )
            flat_list       = RAW_FLAT.objects.filter( session=current_session )
            lamp_list       = RAW_LAMP.objects.filter( session=current_session )

            if  len('bias_list') >= 5 and \
                len('flat_list') >= 10 and \
                len('lamp_list') >= 6:

                night.all_rawcal = True

                reddir=os.path.dirname(os.environ['FEROS_DATA_PATH']+current_session+'/RED/')

                if os.path.isfile(reddir+'/MasterBias.fits'):
                    night.masterbias = True
                if os.path.isfile(reddir+'/Flat.fits'):
                    night.masterflat = True

                all_wavesol = sorted(glob.glob(reddir+'/*.wavsolpars.pkl'))

                for ele in all_wavesol:

                    wavesol_imagename=ele.split('/')[-1].rstrip('.fits')

                    try:
                        wavesolobj  = WAVESOL.objects.get( imagename=wavesol_imagename )
                    except ObjectDoesNotExist:
                        wavesolobj = WAVESOL.objects.create_wavesol(wavesol_imagename)

    time.sleep(60)

