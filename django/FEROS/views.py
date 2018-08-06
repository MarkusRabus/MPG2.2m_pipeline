from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ObjectDoesNotExist

import numpy as np

#from .models import night
#from django.utils import timezone
from astropy.time import Time
from datetime import datetime
from math import floor

import matplotlib
matplotlib.use('Agg') 
import mpld3
from matplotlib import rc
import matplotlib.pyplot as plt

from matplotlib.font_manager import FontProperties
from matplotlib.ticker import MaxNLocator
from matplotlib.dates import DateFormatter,HourLocator

from .models import *
from django import forms




class calplot_Form(forms.Form):
	def __init__(self, *args, **kwargs):
		super(calplot_Form, self).__init__(*args, **kwargs)
		cal_night=get_session()
		session 	= cal_night.date()
		biaslist = []
		biasobj = RAW_BIAS.objects.filter(session=session)
		for ii,lobj in enumerate(biasobj.values_list('imagename')):
			biaslist.append( (lobj[0],lobj[0]) )
		
		self.fields['Images    '] = forms.ChoiceField(
			choices=biaslist )



def index_context():

	context={'good'                 : 'G',
			'bad'                   : 'B',
			'warning'               : 'W',
			'is_true'               : True, 
			'is_false'              : False, 
			'is_none'               : None, }

	try:

		night  = NIGHT.objects.get( calibration_night=get_session() )
		context['cal_night']=night

		# NEW access sql database, to get list
		# other program, e.g. watchdog writes in database and copy files.
		bias_list           = RAW_BIAS.objects.filter( session=get_session() )
		flat_list           = RAW_FLAT.objects.filter( session=get_session() )
		lamp_list           = RAW_LAMP.objects.filter( session=get_session() )
		stat_fibre1_flag    = 'G'
		stat_fibre2_flag    = 'G'
		raw_fibre1_flag     = None
		raw_fibre2_flag     = None

		if night.all_rawcal:
			error_present=True
			raw_fibre1_flag ='G'
			raw_fibre2_flag ='G'

			####
			#  BIAS Level
			####

			rawbias_level = np.mean( [bias_list[0].counts,bias_list[-1].counts] )

			context['rawbias_level']        = '%.2f' % rawbias_level

			if rawbias_level > 150 and rawbias_level < 300:
				context['rawbias_flag'] = 'G'
			else:
				context['rawbias_flag'] = 'B'

			####
			#  FLAT Level
			####

			rawflat1_level  = np.array([flat_list[0].counts1,flat_list[-1].counts1])
			rawflat2_level  = np.array([flat_list[0].counts2,flat_list[-1].counts2])
			#context['rawflat1_level']      = '%.2f/%.2f' % (rawflat1_level[0],rawflat1_level[1])
			#context['rawflat2_level']      = '%.2f/%.2f' % (rawflat2_level[0],rawflat2_level[1])

			context['rawflat1_level']       = '%.0f' % np.mean(rawflat1_level)
			context['rawflat2_level']       = '%.0f' % np.mean(rawflat2_level)      


			if  rawflat1_level[0] > 10000 and rawflat1_level[0] < 50000 and \
				rawflat1_level[1] > 10000 and rawflat1_level[1] < 50000:
				context['rawflat1_flag'] = 'G'
			else:
				context['rawflat1_flag'] = 'B'


			if  rawflat2_level[0] > 10000 and rawflat2_level[0] < 50000 and \
				rawflat2_level[1] > 10000 and rawflat2_level[1] < 50000:
				context['rawflat2_flag'] = 'G'
			else:
				context['rawflat2_flag'] = 'B'


			####
			#  LAMP Level
			####

			rawlamp1_level  = lamp_list[0].counts1
			rawlamp2_level  = lamp_list[0].counts2

			context['rawThArNe1_level']         = '%.0f' % np.mean(rawlamp1_level)
			context['rawThArNe2_level']         = '%.0f' % np.mean(rawlamp2_level)      


			if  rawlamp1_level > 2000 and rawlamp1_level < 50000:
				context['rawThArNe1_flag'] = 'G'
			else:
				context['rawThArNe1_flag'] = 'B'


			if  rawlamp2_level > 2000 and rawlamp2_level < 50000:
				context['rawThArNe2_flag'] = 'G'
			else:
				context['rawThArNe2_flag'] = 'B'
			errormsg='None'

		else:
			error_present=False
			raw_fibre1_flag ='W'
			raw_fibre2_flag ='W'
			errormsg='Not enough calibration frames available. Wait for calibration OB to finish.'      


		context['bias_list']        = bias_list
		context['flat_list']        = flat_list
		context['tharne_list']      = lamp_list

		context['stat_fibre1_flag']     = stat_fibre1_flag
		context['stat_fibre2_flag']     = stat_fibre2_flag
		context['raw_fibre1_flag']      = raw_fibre1_flag
		context['raw_fibre2_flag']      = raw_fibre2_flag
		context['error_present']        = error_present
		context['errormsg']             = errormsg

	except ObjectDoesNotExist:

		night =  NIGHT(calibration_night=Time(2415020.5,format='jd', scale='utc').datetime,all_rawcal = False, masterbias = False, masterflat = False, wavesol_flag = False)
		context['cal_night']=night
		context['error_present']        = True
		context['errormsg']             = 'No FEROS files present!'


	return context






def index(request):
	context = index_context()
	template = loader.get_template('FEROS/index.html')
	return HttpResponse(template.render(context))


def raw(request):
	context = index_context()
	template = loader.get_template('FEROS/raw.html')
	return HttpResponse(template.render(context))


@csrf_exempt
def reduced(request):

	context = index_context()

	context['reduction'] = False
	context['red_obj'] = 0

	template = loader.get_template('FEROS/reduced.html')

	context['wavesol_list'] = WAVESOL.objects.filter( session=get_session() )

	if context['cal_night'].masterbias and \
		context['cal_night'].masterflat and \
		context['cal_night'].wavesol :
		
		context['reduction_message']='Reduced data products present.'
		context['reduction']=True


	else:

		context['reduction_message']='Data reduction in progress ...'
		context['reduction']=False

	return HttpResponse(template.render(context))





@csrf_exempt
def plotcal(request):

	context = index_context()
	cal_night=context['cal_night']

	template = loader.get_template('FEROS/plotcal.html')

	fontP = FontProperties()
	fontP.set_size(9)

	mpl_figure1 = plt.figure(1, figsize=(12, 6))
	mpld3.plugins.clear(mpl_figure1)
	mpld3.plugins.connect(mpl_figure1, mpld3.plugins.Reset(), 
			mpld3.plugins.BoxZoom(), mpld3.plugins.MousePosition(),mpld3.plugins.Zoom())    
	mpl_figure1.clf()
	ax1 = mpl_figure1.add_subplot(1, 1, 1)

	form = calplot_Form()

	biaslist = form.fields['Images    '].choices

	if request.method == 'POST':
		print request.POST['Images    ']
		imagename = request.POST['Images    ']

		if imagename == 'MasterBias':
			reddir=os.path.dirname(data_path+night.strftime(nightfmt)+'_red/')
			imdata =  pf.getdata(reddir+'/MasterBias.fits')
		else:
			rawdir=os.path.dirname(data_path+night.strftime(nightfmt)+'/')
			imdata =  pf.getdata(rawdir+'/'+imagename+'.fits')

	else:
		if len(biaslist) > 0:
			imagename = biaslist[0][1]
			rawdir=os.path.dirname(data_path+night.strftime(nightfmt)+'/')
			imdata =  pf.getdata(rawdir+'/'+imagename+'.fits')
		else:
			context['errormsg'] = 'No BIAS image present !!!!!'
			imdata = np.zeros((4000,2148))

	xpix = np.arange(imdata.shape[1])

	ax1.plot(xpix,imdata[2000,:],'ro',ms=1)
	ax1.plot(xpix,imdata[1000,:],'bo',ms=1)
	ax1.plot(xpix,imdata[3000,:],'go',ms=1)
	#ax1.axvline(x=5)
	#ax1.text(52,150, 'overscan',rotation=90, verticalalignment='center')

	#ax.set_xlim(min_phase,max_phase)
	mm = np.mean(imdata[1000:3000,300:1800])

	ax1.set_ylim(mm-(mm*0.9),mm+(mm*0.9))
	ax1.set_ylabel(r'Counts [ADU]')
	ax1.set_xlabel(r'Pixel')    
	fig_calib = mpld3.fig_to_html(mpl_figure1)

	context['figure_calib'] = fig_calib
	context['form'] = form

	return HttpResponse(template.render(context))





def wavesol(request):
	print request.GET
	context={}
	context['imagename']=request.GET.get("imagename", "")
	template = loader.get_template('FEROS/wavesol.html')
	return HttpResponse(template.render(context))


def contact(request):
	context = index_context()
	template = loader.get_template('FEROS/contact.html')
	return HttpResponse(template.render(context))


def help(request):
	context = index_context()
	template = loader.get_template('FEROS/help.html')
	return HttpResponse(template.render(context))


def spectra(request):
	context = index_context()
	template = loader.get_template('FEROS/spectra.html')
	return HttpResponse(template.render(context))   



def longtermcal(request):

	template = loader.get_template('FEROS/longtermcal.html')

	time_format = '%Y-%m-%d %H:%M:%S'
	#hours = HourLocator(interval=6)
	fontP = FontProperties()
	fontP.set_size(9)

	mpl_figure1 = plt.figure(1, figsize=(12, 6))
	mpld3.plugins.clear(mpl_figure1)
	mpld3.plugins.connect(mpl_figure1, mpld3.plugins.Reset(), 
			mpld3.plugins.BoxZoom(), mpld3.plugins.MousePosition(),mpld3.plugins.Zoom())    
	mpl_figure1.clf()
	ax1 = mpl_figure1.add_subplot(1, 1, 1)

	biasframe = RAW_BIAS.objects.all()
	counts = np.array(biasframe.values_list('counts'))
	obstime = np.array(biasframe.values_list('obstime'))

	ax1.plot_date(obstime, counts,'ko',ms=10)

	#ax.set_xlim(min_phase,max_phase)
	#ax.set_ylim(min_flux,max_flux)
	ax1.set_ylabel(r'raw bias counts')
	ax1.set_xlabel(r'Time') 
	fig_bias = mpld3.fig_to_html(mpl_figure1)


	mpl_figure2 = plt.figure(2, figsize=(12, 6))
	mpld3.plugins.clear(mpl_figure2)
	mpld3.plugins.connect(mpl_figure2, mpld3.plugins.Reset(), 
			mpld3.plugins.BoxZoom(), mpld3.plugins.MousePosition(),mpld3.plugins.Zoom())    
	mpl_figure2.clf()
	ax2 = mpl_figure2.add_subplot(1, 1, 1)

	wavesolframe = WAVESOL.objects.all()
	precision = np.array(wavesolframe.values_list('precision'))
	obstime = np.array(wavesolframe.values_list('obstime'))

	ax2.plot_date(obstime, precision,'ko',ms=10)

	#ax.set_xlim(min_phase,max_phase)
	#ax.set_ylim(min_flux,max_flux)
	ax2.set_ylabel(r'Achievable RV precision')
	ax2.set_xlabel(r'Time') 
	fig_wavesol = mpld3.fig_to_html(mpl_figure2)



	context = { 'figure_wavesol' : fig_wavesol,
				'figure_bias' : fig_bias,
			}

	return HttpResponse(template.render(context))






def longtermrv(request):

	template = loader.get_template('FEROS/longtermrv.html')

	mpl_figure1 = plt.figure(1, figsize=(12, 6))
	mpld3.plugins.clear(mpl_figure1)
	mpld3.plugins.connect(mpl_figure1, mpld3.plugins.Reset(), 
		mpld3.plugins.BoxZoom(), mpld3.plugins.MousePosition(),mpld3.plugins.Zoom())    
	mpl_figure1.clf()
	ax1 = mpl_figure1.add_subplot(1, 1, 1)

	'''
	RVstd = RV_std.objects.filter(std_name='tauCeti')[0]
	
	obstimes    = np.array(RVstd.rvs_set.values_list('dateobs')).flatten()
	rvs         = np.array(RVstd.rvs_set.all().values_list('mes_RV')).flatten()
	error_rvs   = np.array(RVstd.rvs_set.all().values_list('mes_RV_err')).flatten()

	ax1.errorbar(obstimes, rvs,fmt='o',c='k')

	#ax.set_xlim(min_phase,max_phase)
	#ax.set_ylim(min_flux,max_flux)
	ax1.set_ylabel(r'Radial Velocity')
	ax1.set_xlabel(r'Time') 
	'''

	fig_rvstd_tauCeti = mpld3.fig_to_html(mpl_figure1)

	context = { 'figure_rvstd_tauCeti' : fig_rvstd_tauCeti,
			}

	context['errormsg']             = 'Not implemented yet !!!'


	return HttpResponse(template.render(context))


def update_DB(request):

	import glob,os

	context = index_context()
	template = loader.get_template('FEROS/index.html')


	current_session = get_session().strftime(nightfmt)
	src_path 		= os.environ['DIRECTORY_TO_WATCH'] + current_session
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
			hdr['HIERARCH ESO TPL NAME'] in [HIERARCH_ESO_TPL_NAME['bias'],HIERARCH_ESO_TPL_NAME['flat'],HIERARCH_ESO_TPL_NAME['lamp']]:

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
			bias_list 		= RAW_BIAS.objects.filter( session=current_session )
			flat_list 		= RAW_FLAT.objects.filter( session=current_session )
			lamp_list 		= RAW_LAMP.objects.filter( session=current_session )

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
						wavesolobj = WAVESOL.objects.create_wavesol(ele)


	return HttpResponse(template.render(context))








