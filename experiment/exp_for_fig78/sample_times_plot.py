import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


from matplotlib.backends.backend_pdf import PdfPages


with PdfPages("python2.pdf") as pdf:
    a1 =[5.96,5.78,6.05,6.38,6.82,7.8,
         7.42,7.84,7.42,8.2,7.84,7.98,
         8.26,8.45,8.36,8.45,8.46,8.48
    ]#18



    a2=[	4.47,	5.19,	5.94,	5.47,	4.97,	5.47,	6.12,6.28,
            6.51,	6.47,	6.48, 6.47
    ]#

    fig, ax = plt.subplots(1,1,figsize=(8,4))

    plt.plot(list(range(29-len(a1),29)),a1,c='b',marker='o')
    plt.plot(list(range(29-len(a2),29)),a2,c='r',marker='o')

    plt.plot([29-len(a1) for _ in range(10)],[a1[0]/9*i for i in range(10)],':',c='b')


    plt.fill_between([0,29-len(a1)], [(a1[0]+a2[0])/2 ,(a1[0]+a2[0])/2], [
        (3*a1[0]-a2[0])/2,(3*a1[0]-a2[0])/2], label='fill', alpha=.5, color='b')

    plt.plot([29-len(a2) for _ in range(10)],[a2[0]/9*i for i in range(10)],':',c='r')
    plt.fill_between([0,29-len(a2)], [0,0], [
        (a1[0]+a2[0])/2 ,(a2[0]+a1[0])/2], label='fill', alpha=.5, color='r')


    # plt.plot(list(range(29-len(a3),29)),a3,c='g',marker='o')
    #
    # plt.plot([29-len(a3) for _ in range(10)],[a3[0]/9*i for i in range(10)],':',c='g')
    # plt.fill_between([0,29-len(a3)], [0,0], [
    #     (a3[0]+a2[0])/2 ,(a2[0]+a3[0])/2], label='fill', alpha=.5, color='g')

    plt.xticks(range(29))
    plt.legend(["OLPart_WithContext","OLPart_WithoutContext"], fontsize=18,ncol=3,bbox_to_anchor=(1.02,1.2))

    ax.xaxis.set_major_locator(ticker.MultipleLocator(base=5))



    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')

    ax.xaxis.set_ticks_position('bottom')
    ax.spines['bottom'].set_position(('data',0))
    ax.yaxis.set_ticks_position('left')
    ax.spines['left'].set_position(('data',0))


    plt.xticks(fontsize=24)
    plt.yticks(fontsize=24)
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    ax.set_ylabel("IPC", fontsize=24)
    ax.set_xlabel("Sample Times", fontsize=24)
    plt.tight_layout()
    # pdf.savefig()
    plt.show()

