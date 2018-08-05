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

HIERARCH_ESO_TPL_NAME = [   'FEROS bias',
                            'FEROS flatfield',
                            'FEROS ThAr+Ne wavelength calibration',
                            'FEROS obs.object-cal',
                        ]






def trigger_ceres():

    try:
        night  = NIGHT.objects.get( calibration_night=get_session() )
        if night.all_rawcal:
            print 'DATA REDUCTION triggered'
    except ObjectDoesNotExist:
    	print 'NIGHT does not exist'


def trigger_folder(src_path):

    current_session = get_session().strftime(nightfmt)

    if current_session == src_path.split('/')[-1]:
        copy_path       = copy2root+get_session().strftime(nightfmt)+'/RAW/'
        if not os.path.exists(copy_path):
            os.makedirs(copy_path)
    else:

        print '---------------------------------------------------------------'
        print 'Session and Remote night folder are different !!!!'
        print get_session().strftime(nightfmt)
        print src_path.split('/')[-2]
        print '---------------------------------------------------------------'


def trigger_copy(src_path):

    current_session = get_session().strftime(nightfmt)
    if current_session == src_path.split('/')[-2]:

        filename        = src_path.split('/')[-1]
        copy_path       = copy2root+get_session().strftime(nightfmt)+'/RAW/'

        if not os.path.exists(copy_path):
            os.makedirs(copy_path)

        if filename.split('.')[0] == 'FEROS':

            hdr = pf.getheader(src_path)

            if normal_obsmode['HIERARCH ESO DET READ CLOCK'] == hdr['HIERARCH ESO DET READ CLOCK'] and \
                normal_obsmode['CDELT1'] == hdr['CDELT1'] and \
                normal_obsmode['CDELT2'] == hdr['CDELT2'] and \
                hdr['HIERARCH ESO TPL NAME'] in HIERARCH_ESO_TPL_NAME:

                cmd='rsync -avz %s %s' %(  src_path, copy_path )
                status = subprocess.call(cmd, shell=True)

		        print '---------------------------------------------------------------'
		        print 'Copy file are:'
		        print src_path
		        print copy_path
		        print '---------------------------------------------------------------'

        else:
            print 'NOT FEROS!!!!'

    else:

        print '---------------------------------------------------------------'
        print 'Session and Remote night folder are different !!!!'
        print get_session().strftime(nightfmt)
        print src_path.split('/')[-2]
        print '---------------------------------------------------------------'






def update_DB():

	try:
	    night  = NIGHT.objects.get( calibration_night=get_session() )
	except ObjectDoesNotExist:
	    night =  NIGHT(calibration_night=get_session(),all_rawcal = False, masterbias = False, masterflat = False, wavesol_flag = False)
	    night.save()

	rawdir=os.path.dirname(data_path+night.date_string+'/RAW/')
	all_images = sorted(glob.glob(rawdir+'/*.fits'))

	for ele in all_images:

		imagename=ele.split('/')[-1].rstrip('.fits')

		try:
		    raw_im  = RAW_IMAGE.objects.get( imagename=imagename )
		except ObjectDoesNotExist:

			hdr=pf.getheader(ele)

			if hdr['HIERARCH ESO TPL NAME'] == HIERARCH_ESO_TPL_NAME['bias']:
				rawobj = RAW_BIAS.objects.create_raw(ele)
				rawob.save()
			elif hdr['HIERARCH ESO TPL NAME'] == HIERARCH_ESO_TPL_NAME['flat']:
				rawobj = RAW_FLAT.objects.create_raw(ele)
				rawobj.save()
			elif hdr['HIERARCH ESO TPL NAME'] == HIERARCH_ESO_TPL_NAME['lamp']:
				rawobj = RAW_LAMP.objects.create_raw(ele)
				rawobj.save()
			else:
				rawobj = RAW_IMAGE.objects.create_raw(ele)
				rawobj.save()


	# check if all calibrations 
	bias_list 		= RAW_BIAS.objects.filter( session=get_session() )
	flat_list 		= RAW_FLAT.objects.filter( session=get_session() )
	lamp_list 		= RAW_LAMP.objects.filter( session=get_session() )

	if  len('bias_list') >= 5 and \
		len('flat_list') >= 10 and \
		len('lamp_list') >= 6:

		night.all_rawcal = True

		reddir=os.path.dirname(data_path+night.date_string+'/RED/')

		if os.path.isfile(reddir+'/MasterBias.fits'):
			night.masterbias = True
		if os.path.isfile(reddir+'/Flat.fits'):
			night.masterflat = True

		all_wavesol = sorted(glob.glob(reddir+'/*.wavsolpars.pkl'))

		for ele in all_wavesol:

			imagename=ele.split('/')[-1].rstrip('.fits')

			try:
			    wavesolobj  = WAVESOL.objects.get( imagename=imagename )
			except ObjectDoesNotExist:
				wavesolobj = WAVESOL.objects.create_wavesol(ele)
















