from __future__ import unicode_literals

from django.db import models
from astropy.time import Time
from astropy.io import fits as pf
import numpy as np
from math import floor
from datetime import datetime

from astropy.modeling.fitting import LevMarLSQFitter
from astropy.modeling import models as gpmodel
from astropy.modeling.models import custom_model

import os


data_path=os.environ['FEROS_DATA_PATH']
nightfmt="%Y-%m-%d"


lamps =(	('FLAT' 	, 'LAMP2'),
			('ThAr' 	, 'LAMP1'),
			('ThAr+Ne'	, 'LAMP3'),
		)

HIERARCH_ESO_TPL_NAME = {	'bias' 			: 'FEROS bias',
							'flat' 			: 'FEROS flatfield',
							'lamp'  		: 'FEROS ThAr+Ne wavelength calibration',
							'object-cal' 	: 'FEROS obs.object-cal'
						}



@custom_model
def model_gaussian2(x, 	amp1a = 15000, amp1b = 15000 , g1a_mean = 20., sigma1=1., 
						amp2a = 15000, amp2b = 15000 , g2a_mean = 40., sigma2=1., 
						offset=200.):

	g1b_mean = g1a_mean + 5
	g2b_mean = g2a_mean + 5

	g1a = gpmodel.Gaussian1D(amp1a, g1a_mean, sigma1)
	g1b = gpmodel.Gaussian1D(amp1b, g1b_mean, sigma1)

	g2a = gpmodel.Gaussian1D(amp2a, g2a_mean, sigma2)
	g2b = gpmodel.Gaussian1D(amp2b, g2b_mean, sigma2)

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




def get_session():
    isnow=Time(datetime.now())
    return Time(floor(isnow.jd),format='jd', scale='utc').datetime


'''
class OBSMODE(models.Model):
	name 			= models.CharField('Obsmode', editable=False, max_length=50, primary_key=True, unique=True)
	clock_speed 	= models.CharField('Detector clock speed', editable=False, max_length=500)
	cdelt1 			= models.IntegerField('CDELT1',editable=False)
	cdelt2 			= models.IntegerField('CDELT2',editable=False)
	gain 			= models.FloatField('Gain',editable=False)
	readout_noise 	= models.FloatField('Readout noise',editable=False)
	readout_time 	= models.FloatField('Readout time',editable=False)
'''

class NIGHT(models.Model):
	calibration_night 	= models.DateTimeField('Night of calibration', editable=False, primary_key=True, unique=True)
	all_rawcal 			= models.BooleanField('All raw calibration frames present', default=False,editable=False)
	masterbias 			= models.BooleanField('Master bias present', default=False,editable=False)
	masterflat 			= models.BooleanField('Master flat present', default=False,editable=False)
	wavesol_flag 		= models.BooleanField('Wavelength solution present', default=False,editable=False)

	def date_string(self):
		return self.calibration_night.strftime(nightfmt)









class RAW_IMAGE_Manager(models.Manager):
	def create_raw(self,path):
		hdr 			= pf.getheader(path)
		#Search for corresponding night:
		night 			= NIGHT.objects.get(calibration_night=get_session())		

		rawim 			= self.create(imagename=path.split('/')[-1].rstrip('.fits'), session=night)
		rawim.path 		= path.rstrip(path.split('/')[-1])
		rawim.exptime 	= hdr['EXPTIME']
		'''
		obsmode = OBSMODE.objects.filter(clock_speed = hdr['HIERARCH ESO DET READ MODE'])
		obsmode = obsmode.filter(cdelt1 = hdr['CDELT1'])
		obsmode = obsmode.filter(cdelt2 = hdr['CDELT2'])
		rawim.obsmode 	= obsmode[0]
		'''
		rawim.binning 	= '%0.1f x %0.1f' % (hdr['CDELT1'],hdr['CDELT2'])
		rawim.obstime 	= Time(hdr['DATE-OBS'], format='isot', scale='utc').datetime


		if hdr['HIERARCH ESO TPL NAME'] == HIERARCH_ESO_TPL_NAME['bias']:
			rawim.imtype = 'bias'
			tmpcounts		= get_rawcounts_level(path,rawim.imtype)
			if tmpcounts is not None:
				rawim.counts 	= int(tmpcounts)
			else:
				rawim.counts 	= tmpcounts

		elif hdr['HIERARCH ESO TPL NAME'] == HIERARCH_ESO_TPL_NAME['flat']:
			rawim.imtype = 'flat'
			tmpcounts		= get_rawcounts_level(path,rawim.imtype)
			if tmpcounts is not None:
				rawim.counts1 	= int(tmpcounts[0])
				rawim.counts2 	= int(tmpcounts[1])
			else:
				rawim.counts 	= tmpcounts

		elif hdr['HIERARCH ESO TPL NAME'] == HIERARCH_ESO_TPL_NAME['lamp']:
			rawim.imtype = 'lamp'
			tmpcounts		= get_rawcounts_level(path,rawim.imtype)
			if tmpcounts is not None:
				rawim.counts1 	= int(tmpcounts[0])
				rawim.counts2 	= int(tmpcounts[1])
			else:
				rawim.counts 	= tmpcounts

		elif hdr['HIERARCH ESO TPL NAME'] == HIERARCH_ESO_TPL_NAME['object-cal']:
			rawim.imtype = 'object-cal'

		else:
			rawim.imtype = 'undefined ???'

		return rawim


class RAW_IMAGE(models.Model):

	imagename       = models.CharField('Image name', editable=False,
						primary_key=True, unique=True, max_length=250)
	path            = models.FilePathField('Fits file path', editable=False,
						max_length=250,null=True)
	exptime         = models.FloatField('Exposure time',editable=False,default=0.0)
	obstime         = models.DateTimeField('Obs. date & time',editable=False,null=True)
	#obsmode         = models.ForeignKey(OBSMODE, on_delete=models.CASCADE)
	binning         = models.CharField('Binning', editable=False, max_length=3,null=True)
	session			= models.ForeignKey(NIGHT, on_delete=models.CASCADE)
	imtype         	= models.CharField('Image type [bias, flat, wave, lamp, ThAr, object-cal, undefined]', editable=False, max_length=4,null=True)

	objects = RAW_IMAGE_Manager()

class RAW_BIAS(RAW_IMAGE):
	counts       	= models.FloatField('Counts',editable=False,default=0.0)
	objects = RAW_IMAGE_Manager()

class RAW_FLAT(RAW_IMAGE):
	counts1       	= models.FloatField('Counts fibre 1',editable=False,default=0.0)
	counts2       	= models.FloatField('Counts fibre 2',editable=False,default=0.0)
	objects = RAW_IMAGE_Manager()

class RAW_LAMP(RAW_IMAGE):
	counts1       	= models.FloatField('Counts fibre 1',editable=False,default=0.0)
	counts2       	= models.FloatField('Counts fibre 2',editable=False,default=0.0)
	objects = RAW_IMAGE_Manager()











class WAVESOL_Manager(models.Manager):

	def create_wavesol(self,path):

		#Search for corresponding night:
		night 			= NIGHT.objects.get(calibration_night=get_session())		

		wavesol 			= self.create( imagename=path.split('/')[-1].rstrip('.wavsolpars.pkl'), session=night )
		wavesol.path 		= path.rstrip(path.split('/')[-1])
		pdict 				= pickle.load(open(path,'r'))

		wavesol.rms 		= pdict['rms_ms_co']
		wavesol.obstime 	= Time(pdict['mjd'], format='mjd').datetime
		wavesol.N_l 		= len(pdict['G_wav_co'])
		wavesol.precision 	= pdict['rms_ms_co']/np.sqrt( len(pdict['G_wav_co']) )

		return wavesol

class WAVESOL(models.Model):

	imagename       = models.CharField('Image name', editable=False,
						primary_key=True, unique=True, max_length=250)
	path            = models.FilePathField('Pickle file path', editable=False,
						max_length=250,null=True)
	rms         	= models.FloatField('Final RMS',editable=False,default=0.0)
	obstime         = models.DateTimeField('Obs. date & time',editable=False,null=True)
	N_l       		= models.FloatField('Number of lines',editable=False,default=0.0)
	precision 		= models.FloatField('Achievable precision',editable=False,default=0.0)
	session			= models.ForeignKey(NIGHT, on_delete=models.CASCADE)
	objects = WAVESOL_Manager()



















class RED_SPECTRUM(models.Model):
	imagename       = models.CharField('Image name', editable=False,
						primary_key=True, unique=True, max_length=250)
	path            = models.FilePathField('Fits file path', editable=False,
						max_length=250)    
	session			= models.ForeignKey(NIGHT, on_delete=models.CASCADE)
	raw_spectra 	= models.ForeignKey(RAW_IMAGE, on_delete=models.CASCADE)




class OBJECT(models.Model):

	object_name 	= models.CharField('Object name', editable=False, max_length=100)
	V_mag 			= models.FloatField('V mag.',editable=False,blank=True,null=True)
	ra 				= models.FloatField('RA', editable=False)
	dec 			= models.FloatField('DEC', editable=False)
	is_RVstd 		= models.BooleanField('Target is RV standard star',default=False, editable=False)
	raw_spectra 	= models.ForeignKey(RAW_IMAGE, on_delete=models.CASCADE)
	red_spectra 	= models.ForeignKey(RED_SPECTRUM, on_delete=models.CASCADE)
	CCF_plot        = models.FilePathField('Path to the CCF', editable=False, max_length=250)    	

	def get_gen_fields(self):
		"""Returns a list of all field names on the instance."""
		fields = []
		for f in self._meta.fields:

			fname = f.name        
			# resolve picklists/choices, with get_xyz_display() function
			get_choice = 'get_'+fname+'_display'
			if hasattr( self, get_choice):
				value = getattr( self, get_choice)()
			else:
				try :
					value = getattr(self, fname)
				except User.DoesNotExist:
					value = None

			# only display fields with values and skip some fields entirely
			if value and f.name not in ('std_name') :

				fields.append(
				  {
				   'label':f.verbose_name, 
				   'name':f.name, 
				   'value':value,
				  }
				)
		return fields




class RVs(models.Model):
	class Meta:
			ordering = ['dateobs']	

	target_name 	= models.ForeignKey(OBJECT)

	dateobs			= models.FloatField(r'Obs. date [BJD]')
	mes_RV 			= models.FloatField(r'meas. RV')
	mes_RV_err 		= models.FloatField(r'meas. RV err.')
	bisector		= models.FloatField(r'bisector span', blank=True,null=True)
	bisector_err	= models.FloatField(r'error bisector span', blank=True,null=True)	
	Teff			= models.FloatField(r'effective temperature', blank=True,null=True)
	logg			= models.FloatField(r'log(g)', blank=True,null=True)
	feh				= models.FloatField(r'[Fe/H]', blank=True,null=True)
	vsini			= models.FloatField(r'v sin i', blank=True,null=True)
	peak			= models.FloatField(r'lowest point CCF', blank=True,null=True)
	stdCCF			= models.FloatField(r'standard deviation CCF', blank=True,null=True)
	snr				= models.FloatField(r'SNR at ~5150 Angstrom', blank=True,null=True)
	exptime			= models.FloatField(r'Exp. time', blank=True,null=True)





