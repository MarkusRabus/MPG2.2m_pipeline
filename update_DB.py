from astropy.io import fits as pf
import glob
from astropy.modeling.fitting import LevMarLSQFitter

import os
import sys
import django
from django.core.exceptions import ObjectDoesNotExist


nightfmt="%Y-%m-%d"
data_path = os.environ['FEROS_DATA_PATH']
sys.path.append(os.environ['DJANGO_PROJECT_PATH'])
from django.apps import apps
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MPG2p2m.settings")
django.setup()

from FEROS.models import *



@custom_model
def model_gaussian2(x, 	amp1a = 15000, amp1b = 15000 , g1a_mean = 20., sigma1=1., 
						amp2a = 15000, amp2b = 15000 , g2a_mean = 40., sigma2=1., 
						offset=200.):

	g1b_mean = g1a_mean + 5
	g2b_mean = g2a_mean + 5

	g1a = apmodel.Gaussian1D(amp1a, g1a_mean, sigma1)
	g1b = apmodel.Gaussian1D(amp1b, g1b_mean, sigma1)

	g2a = apmodel.Gaussian1D(amp2a, g2a_mean, sigma2)
	g2b = apmodel.Gaussian1D(amp2b, g2b_mean, sigma2)

	return  g1a(x) + g1b(x) + g2a(x) + g2b(x) + offset




def get_rawcounts_level(path,imtype):

	if imtype == 'bias':
		tmpdata = pf.getdata(path)
		return np.mean(tmpdata[1000:3000,300:1800])

	elif imtype == 'flat':
		gauss_fitter 			= LevMarLSQFitter()

		specdata1 = pf.getdata(path)[2050,1050:1120]

		feros_gauss = model_gaussian2(	amp1a = np.max(specdata1), amp1b = np.max(specdata1) , g1a_mean = 23., sigma1=1.5, 
								amp2a = np.max(specdata1), amp2b = np.max(specdata1) , g2a_mean = 41., sigma2=1.5, 
								offset=200.)

		x = np.linspace(0, specdata1.shape[0], specdata1.shape[0])
		fitted_gauss1 = gauss_fitter(feros_gauss, x, specdata1)	
		return [np.max([fitted_gauss1.amp1a,fitted_gauss1.amp1b]), 
				np.max([fitted_gauss1.amp2a,fitted_gauss1.amp2b])]

	elif imtype == 'lamp':
		gauss_fitter 			= LevMarLSQFitter()

		specdata1 = pf.getdata(path)[2059,1000:1070]

		feros_gauss = model_gaussian2(	amp1a = np.max(specdata1), amp1b = np.max(specdata1) , g1a_mean = 23., sigma1=1.5, 
								amp2a = np.max(specdata1), amp2b = np.max(specdata1) , g2a_mean = 41., sigma2=1.5, 
								offset=200.)

		x = np.linspace(0, specdata1.shape[0], specdata1.shape[0])
		fitted_gauss1 = gauss_fitter(feros_gauss, x, specdata1)

		return [np.max([fitted_gauss1.amp1a,fitted_gauss1.amp1b]),
				np.max([fitted_gauss1.amp2a,fitted_gauss1.amp2b])]








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
















